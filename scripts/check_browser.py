#!/usr/bin/env python3
"""Desktop/mobile QA against a disposable local server; stores review screenshots."""
from __future__ import annotations

import functools
import http.server
import json
import os
from pathlib import Path
import threading

from playwright.sync_api import sync_playwright
from build import OUT, ROOT, projects


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_): pass


def check():
    results = ROOT / 'test-results'
    results.mkdir(exist_ok=True)
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(OUT)))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    origin = f'http://127.0.0.1:{server.server_port}'
    failures = []; observations = []
    try:
        with sync_playwright() as playwright:
            executable = os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE')
            browser = playwright.chromium.launch(executable_path=executable or None)
            page = browser.new_page(viewport={'width':1440,'height':1000}, device_scale_factor=1)
            page.on('pageerror', lambda error: failures.append(str(error)))
            page.on('response', lambda response: failures.append(f'HTTP {response.status}: {response.url}') if response.status >= 400 else None)
            page.goto(origin, wait_until='networkidle')
            count = len([p for p in projects() if p['status']=='open'])
            assert page.locator('h1').count() == 1, 'Exactly one H1 per page'
            assert page.locator('main').count() == 1, 'Exactly one main landmark'
            page.screenshot(path=str(results/'desktop-home.png'), full_page=False)
            page.keyboard.press('Tab')
            assert page.locator('.skip-link').evaluate('(el) => el === document.activeElement')
            page.get_by_role('link', name='Job vacancies').click()
            assert page.locator('h1').inner_text() == 'Jobs'
            page.get_by_role('link', name='Funding and fellowships', exact=True).click()
            assert page.locator('h1').inner_text() == 'Funding and fellowships'
            page.get_by_role('link', name='contact us with your research idea and the programme you have in mind').click()
            assert page.url.endswith('/apply.html#fellowships-and-research-visits')
            assert page.get_by_role('heading', name='Fellowships and research visits', exact=True).is_visible()
            page.goto(origin, wait_until='networkidle')
            page.get_by_role('link', name='Browse projects').click()
            assert page.locator('h1').inner_text() == 'BSc/MSc projects and research internships'
            assert page.locator('.project-card:visible').count() == count
            search = page.get_by_label('Find a question, method or field of study')
            for query, expected in [('engineering','smartphone-corneal-irradiance'),('journalism','clock-change-media'),('NLP','ai-light-interventions'),('psychology','darkness-dose'),('Git','')]:
                search.fill(query)
                if expected:
                    assert page.locator(f'.project-card:visible a[href*="{expected}"]').count() == 1, query
            search.fill('definitely-no-such-project')
            assert page.locator('.project-card:visible').count() == 0
            assert page.get_by_text('No projects match that search.').is_visible()
            page.get_by_role('button',name='Clear search and filters').click()
            assert page.locator('.project-card:visible').count() == count
            page.get_by_label('Where would you like to work?').select_option('Remote')
            for card in page.locator('.project-card:visible').all():
                assert 'Remote' in card.get_attribute('data-locations')
            assert page.locator('.project-card:visible').count() < count
            search.fill('Soziologie')
            assert page.locator('.project-card:visible a[href*="schlaf-gesellschaft"]').count() == 1
            page.reload(wait_until='networkidle')
            assert search.input_value() == 'Soziologie'
            assert page.get_by_label('Where would you like to work?').input_value() == 'Remote'
            page.goto(origin+'/student-projects.html?q=engineering', wait_until='networkidle')
            assert page.locator('.project-card:visible').count() > 0
            page.locator('.project-card:visible h3 a').first.click()
            with page.expect_download() as download:
                page.get_by_role('link', name='Download one-page PDF').click()
            assert download.value.suggested_filename.endswith('.pdf')
            assert download.value.failure() is None
            routes = ['/','/student-projects.html','/jobs.html','/about.html','/expectations.html','/funding.html','/apply.html','/programmes.html','/404.html'] + [f'/projects/{p["slug"]}/' for p in projects()]
            for width,height in [(1440,1000),(390,844),(320,740)]:
                page.set_viewport_size({'width':width,'height':height})
                for route in routes:
                    page.goto(origin+route, wait_until='networkidle')
                    assert page.locator('h1').count() == 1, route
                    assert page.locator('main').count() == 1, route
                    overflow = page.evaluate('document.documentElement.scrollWidth > innerWidth + 1')
                    assert not overflow, f'Horizontal overflow at {width}px: {route}'
                    broken = page.locator('img').evaluate_all('(imgs) => imgs.filter(i => !i.complete || !i.naturalWidth).map(i => i.src)')
                    assert not broken, broken
                    if route.startswith('/projects/schlaf-'):
                        assert page.locator('html').get_attribute('lang') == 'de'
                        assert page.get_by_role('link',name='Projektblatt als PDF herunterladen').count() == 1
                        assert page.get_by_role('heading', name='Die Frage',exact=True).count() == 1
                    if (width,route) in [(390,'/'),(390,'/student-projects.html'),(390,'/jobs.html'),(390,'/funding.html'),(1440,'/funding.html'),(390,'/projects/smartphone-corneal-irradiance/'),(1440,'/projects/darkness-dose/'),(1440,'/projects/schlaf-gesellschaft-unterricht/')]:
                        name = route.strip('/').replace('/','-') or 'home'
                        page.screenshot(path=str(results/f'{width}-{name}.png'), full_page=True)
                observations.append(f'{len(routes)} routes checked at {width} × {height}')
                print(observations[-1], flush=True)
            # No-JS users still receive the complete catalogue and working links.
            context = browser.new_context(java_script_enabled=False)
            plain = context.new_page(); plain.goto(origin)
            plain.get_by_role('link', name='Browse projects').click()
            assert plain.locator('.project-card').count() == count
            assert plain.locator('noscript').is_visible()
            context.close()
            # Regression: direct HTML opening must not navigate to directories.
            offline = browser.new_page(viewport={'width':556,'height':851})
            offline.on('pageerror', lambda error: failures.append('Local HTML: ' + str(error)))
            home_file = (OUT / 'index.html').as_uri()
            offline.goto(home_file)
            offline.get_by_role('link', name='Job vacancies').click()
            assert offline.url == (OUT / 'jobs.html').as_uri()
            offline.get_by_role('link', name='Funding and fellowships', exact=True).click()
            assert offline.url == (OUT / 'funding.html').as_uri()
            offline.get_by_role('link', name='contact us with your research idea and the programme you have in mind').click()
            assert offline.url == (OUT / 'apply.html').as_uri() + '#fellowships-and-research-visits'
            offline.get_by_role('navigation').get_by_role('link', name='Join', exact=True).click()
            assert offline.url == home_file
            offline.get_by_role('link', name='Browse projects').click()
            catalogue_file = (OUT / 'student-projects.html').as_uri()
            assert offline.url == catalogue_file
            for i in range(count):
                offline.locator('.project-card h3 a').nth(i).click()
                assert offline.url.endswith('/index.html') and '/projects/' in offline.url
                assert offline.locator('.project-body h2').count() == 4
                offline.locator('.back-link').click()
                assert offline.url == catalogue_file
            for filename, heading in [('about.html','About the unit'),('expectations.html','General expectations'),('funding.html','Funding and fellowships'),('jobs.html','Jobs')]:
                offline.goto((OUT / filename).as_uri())
                assert offline.locator('h1').inner_text() == heading
                offline.get_by_role('navigation').get_by_role('link',name='Student projects',exact=True).click()
                assert offline.url == catalogue_file
            offline.goto((OUT / 'programmes.html').as_uri())
            offline.locator('.programme-list a').filter(has_text='Engineering').first.click()
            assert offline.url.startswith(catalogue_file + '?q=')
            assert 0 < offline.locator('.project-card:visible').count() < count
            offline.get_by_label('Find a question, method or field of study').fill('darkness')
            assert offline.locator('.project-card:visible a[href*="darkness-dose"]').count() == 1
            observations.append(f'{count} project cards and return links checked using file:// URLs')
            offline.close(); browser.close()
        assert not failures, '\n'.join(failures)
        report = {'result':'PASS','projects':count,'layout_checks':observations,'behaviour':['Homepage routes to student projects, jobs and fellowship enquiries','Search by hidden metadata','Search + location intersection','Empty state + reset','URL persistence','Keyboard skip link','PDF download','German language','No-JavaScript catalogue','Local HTML navigation and programme search'],'browser_errors':failures}
        (results/'browser-report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
    finally:
        server.shutdown(); server.server_close()


if __name__ == '__main__': check()
