#!/usr/bin/env python3
"""Quarto hooks and validation. Project QMD files are the only project records."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit

import yaml
from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '_site'
GEN = ROOT / '_generated'
LOGO = ROOT / 'assets/tscn-logo.png'
LOGO_URL = 'https://raw.githubusercontent.com/tscnlab/Templates/main/logo/logo_with_text-01.png'
LOGO_SHA = 'ad721549a8fd502f376ead0afa3426265bca46491607bfea3043db5e7dbb6ee3'
LOCATIONS = {'Tübingen', 'Munich', 'Remote'}
FORMATS = {"Master's thesis", 'Research internship', 'Erasmus+ research placement', 'Engineering project'}
THEMES = {'Human photobiology', 'Measuring the environment', 'Sleep, brain and sensory function', 'Clinical translation', 'Circadian health in society'}
REQUIRED = {'title', 'subtitle', 'slug', 'lang', 'location', 'formats', 'primary-theme', 'backgrounds', 'methods', 'status', 'disclosure'}
HEADINGS = {'en': ['The question', 'The project', 'What you will do', 'Possible scope'], 'de': ['Die Frage', 'Das Projekt', 'Ihre Aufgaben', 'Möglicher Umfang']}
PRIVATE = re.compile(r'(^|[/_.-])(private|confidential|protocols|pilot-data|implementation-notes|\.env)([/_.-]|$)', re.I)
MD = MarkdownIt('commonmark', {'html': False})


def read_project(path: Path) -> dict:
    text = path.read_text(encoding='utf-8')
    match = re.fullmatch(r'---\n(.*?)\n---\n(.*)', text, re.S)
    if not match:
        raise ValueError(f'{path}: expected YAML front matter')
    data = yaml.safe_load(match[1])
    if not isinstance(data, dict):
        raise ValueError(f'{path}: metadata must be a mapping')
    return {**data, 'body': match[2].strip(), 'path': path}


def validate_record(p: dict) -> None:
    name = str(p['path'].relative_to(ROOT)) if p['path'].is_relative_to(ROOT) else str(p['path'])
    missing = REQUIRED - p.keys()
    if missing:
        raise ValueError(f'{name}: missing metadata {sorted(missing)}')
    if not isinstance(p['slug'], str) or not re.fullmatch(r'[a-z]+(?:-[a-z]+)*', p['slug']):
        raise ValueError(f'{name}: slug must contain only semantic lowercase words, no digits')
    if p['path'].parent.name != p['slug']:
        raise ValueError(f'{name}: slug must match directory')
    if p['lang'] not in HEADINGS:
        raise ValueError(f'{name}: lang must be en or de')
    for key in ('title', 'subtitle', 'primary-theme'):
        if not isinstance(p[key], str) or not p[key].strip():
            raise ValueError(f'{name}: {key} must be non-empty text')
    if re.match(r'^(?:project\s*)?(?:\d+|[IVX]+)[.:-]\s', p['title'], re.I):
        raise ValueError(f'{name}: no numbered project titles')
    for key in ('location', 'formats', 'backgrounds', 'methods'):
        if not isinstance(p[key], list) or not p[key] or any(not isinstance(x, str) or not x.strip() for x in p[key]):
            raise ValueError(f'{name}: {key} must be a non-empty list of strings')
        if len(set(p[key])) != len(p[key]):
            raise ValueError(f'{name}: duplicate {key}')
    if not set(p['location']) <= LOCATIONS or not set(p['formats']) <= FORMATS:
        raise ValueError(f'{name}: unsupported location or format')
    if p['primary-theme'] not in THEMES:
        raise ValueError(f'{name}: unsupported primary theme')
    if p['status'] not in {'open', 'paused', 'closed'} or p['disclosure'] not in {'standard', 'teaser'}:
        raise ValueError(f'{name}: unsupported status or disclosure')
    headings = re.findall(r'^## (.+)$', p['body'], re.M)
    if headings != HEADINGS[p['lang']]:
        raise ValueError(f'{name}: use the four documented section headings, in order')
    # A deliberately small common Markdown subset keeps both renderers faithful.
    supported = {'heading_open', 'heading_close', 'paragraph_open', 'paragraph_close', 'inline', 'bullet_list_open', 'bullet_list_close', 'list_item_open', 'list_item_close'}
    for token in MD.parse(p['body']):
        if token.type not in supported or (token.type == 'heading_open' and token.tag != 'h2'):
            raise ValueError(f'{name}: unsupported Markdown block {token.type}; use paragraphs, H2 headings and bullets')
        if token.type == 'inline' and any(t.type not in {'text','softbreak','strong_open','strong_close','em_open','em_close','link_open','link_close','code_inline'} for t in token.children or []):
            raise ValueError(f'{name}: unsupported inline Markdown')
    if len(p['body'].split()) > 330:
        raise ValueError(f'{name}: keep the advert under 330 words for a legible A4 page')
    if re.search(r'\{\{|<[/!a-zA-Z]|^```', p['body'], re.M):
        raise ValueError(f'{name}: raw HTML, includes and executable code are not supported in public adverts')


def projects() -> list[dict]:
    paths = sorted((ROOT / 'projects').glob('*/index.qmd'))
    if not paths:
        raise ValueError('No project sources found')
    extra = set((ROOT / 'projects').rglob('*.qmd')) - set(paths)
    if extra:
        raise ValueError(f'Noncanonical project QMD files: {extra}')
    records = [read_project(path) for path in paths]
    for p in records:
        validate_record(p)
    if len({p['slug'] for p in records}) != len(records):
        raise ValueError('Duplicate project slugs')
    return records


def shared() -> dict:
    data = yaml.safe_load((ROOT / 'shared/content.yml').read_text(encoding='utf-8'))
    updated = date.fromisoformat(str(data['last_updated']))
    data['last_updated'] = updated.isoformat()
    months = {
        'en': 'January February March April May June July August September October November December'.split(),
        'de': 'Januar Februar März April Mai Juni Juli August September Oktober November Dezember'.split(),
    }
    for lang, names in months.items():
        data[lang]['updated_date'] = f'{updated.day}{"." if lang == "de" else ""} {names[updated.month - 1]} {updated.year}'
    return data


def ensure_logo() -> None:
    if not LOGO.exists():
        LOGO.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(LOGO_URL, timeout=30) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != LOGO_SHA:
            raise ValueError('Canonical logo changed; review upstream before updating the digest')
        LOGO.write_bytes(data)
    if hashlib.sha256(LOGO.read_bytes()).hexdigest() != LOGO_SHA:
        raise ValueError('Logo differs from the verified canonical asset')


def check_tracked_private() -> None:
    result = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('Cannot inspect tracked files for private material: ' + result.stderr)
    bad = [s for s in result.stdout.split('\0') if s and (PRIVATE.search(s) or Path(s).suffix in {'.pem', '.key'})]
    if bad:
        raise ValueError(f'Private material must not be tracked: {bad}')


def pitch(p: dict) -> str:
    return next(t.content for t in MD.parse(p['body']) if t.type == 'inline' and t.map and t.map[0] > 0)


def prepare() -> None:
    ps = projects(); ensure_logo(); check_tracked_private(); s = shared()
    GEN.mkdir(exist_ok=True)
    (GEN / 'shared.json').write_text(json.dumps(s, ensure_ascii=False), encoding='utf-8')
    for name in ('about', 'expectations', 'funding', 'apply'):
        (GEN / f'{name}.md').write_text(s['en'][name], encoding='utf-8')
    (GEN / 'jobs-status.md').write_text(s['en']['jobs_status'] + '\n', encoding='utf-8')
    e = html.escape
    featured = ['darkness-dose', 'smartphone-corneal-irradiance', 'temporal-autonomy']
    ps.sort(key=lambda p: (featured.index(p['slug']) if p['slug'] in featured else len(featured), p['title'].casefold()))
    open_projects = [p for p in ps if p['status'] == 'open']
    cards = []
    for p in open_projects:
        de = p['lang'] == 'de'
        loc = ' · '.join('München' if de and l == 'Munich' else l for l in p['location'])
        haystack = ' '.join([p['title'], p['subtitle'], p['body'], p['primary-theme'], p['lang'], *p['backgrounds'], *p['methods'], *p['location'], *p['formats']])
        text = pitch(p)
        if len(text) > 230:
            text = text[:227].rsplit(' ', 1)[0] + '…'
        cards.append(f'<article class="project-card" lang="{p["lang"]}" data-search="{e(haystack, quote=True)}" data-locations="{e("|".join(p["location"]), quote=True)}"><p class="card-location">{e(loc)}</p><h3><a href="/projects/{p["slug"]}/">{e(p["title"])}</a></h3><p class="card-pitch">{e(text)}</p><div class="card-end"><span>{"Projekt auf Deutsch" if de else ("Engineering & research" if "Engineering project" in p["formats"] else "Student research project")}</span><span class="arrow" aria-hidden="true">↗</span></div></article>')
    catalogue = f'''```{{=html}}
<section aria-labelledby="browse-title">
<div class="browse-heading"><h2 id="browse-title">Available projects</h2><span class="result-count" id="result-count" role="status" aria-live="polite">{len(cards)} projects</span></div>
<div class="search-controls"><div class="field"><label for="project-search">Find a question, method or field of study</label><input id="project-search" type="search" placeholder="Try psychology, light, engineering…" aria-describedby="search-help" autocomplete="off"></div><div class="field"><label for="location-filter">Where would you like to work?</label><select id="location-filter"><option value="">All locations</option><option>Tübingen</option><option>Munich</option><option>Remote</option></select></div></div>
<p id="search-help" class="search-help">Search across titles, methods and suitable backgrounds. Locations and scope are agreed individually.</p>
<noscript><p>All projects are listed below. Search and location filtering require JavaScript.</p></noscript>
<div class="project-grid">{''.join(cards)}</div>
<div id="no-results" class="empty-state" hidden><h3>No projects match that search.</h3><p>Try a broader topic or another location.</p><button class="reset-search" id="reset-search" type="button">Clear search and filters</button></div>
</section>
```
'''
    (GEN / 'catalogue.md').write_text(catalogue, encoding='utf-8')
    backgrounds = sorted({b for p in open_projects for b in p['backgrounds']}, key=str.casefold)
    programme_links = ''.join(f'<li><a href="/student-projects.html?q={quote(b)}">{e(b)} <small>{sum(b in p["backgrounds"] for p in open_projects)} →</small></a></li>' for b in backgrounds)
    (GEN / 'programmes.md').write_text('```{=html}\n<ul class="programme-list">' + programme_links + '</ul>\n```\n', encoding='utf-8')
    print(f'Validated {len(ps)} canonical project sources; prepared shared content and catalogue.')


def pdfs() -> None:
    from pdfs import render_pdf
    ps = projects(); ensure_logo(); s = shared()
    for p in ps:
        target = OUT / 'projects' / p['slug'] / 'advert.pdf'
        target.parent.mkdir(parents=True, exist_ok=True)
        render_pdf(p, s, LOGO, target)
    print(f'Generated {len(ps)} standalone A4 PDF adverts.')


def portable_links() -> None:
    """Use explicit relative files, including index.html, for offline navigation.

    Quarto normally shortens directory-index links for HTTP hosting. A file://
    browser does not resolve those directories to index.html automatically.
    Keep published routes intact while making the rendered folder browsable.
    """
    for page in OUT.rglob('*.html'):
        soup = BeautifulSoup(page.read_text(encoding='utf-8'), 'html.parser')
        changed = False
        for link in soup.select('a[href]'):
            url = urlsplit(link['href'])
            if url.scheme or url.netloc or not url.path:
                continue
            target = (OUT / unquote(url.path).lstrip('/') if url.path.startswith('/') else page.parent / unquote(url.path)).resolve()
            directory = target.is_dir()
            if directory:
                target /= 'index.html'
            if (directory or url.path.startswith('/')) and target.is_relative_to(OUT.resolve()):
                relative = Path(os.path.relpath(target, page.parent)).as_posix()
                link['href'] = urlunsplit(('', '', quote(relative, safe='/.-'), url.query, url.fragment))
                changed = True
        if changed:
            page.write_text(str(soup), encoding='utf-8')


def validate_output() -> None:
    ps = projects(); errors = []; pages = list(OUT.rglob('*.html')); s = shared()
    for p in ps:
        folder = OUT / 'projects' / p['slug']
        if not (folder / 'index.html').is_file():
            errors.append(f'Missing HTML: {p["slug"]}')
        pdf = folder / 'advert.pdf'
        if not pdf.is_file():
            errors.append(f'Missing PDF: {p["slug"]}'); continue
        reader = PdfReader(pdf)
        if len(reader.pages) != 1:
            errors.append(f'PDF must have exactly one page: {pdf}')
        for page in reader.pages:
            if abs(float(page.mediabox.width) - 595.276) > 1 or abs(float(page.mediabox.height) - 841.89) > 1:
                errors.append(f'Not A4: {pdf}')
        text = reader.pages[0].extract_text()
        norm = lambda t: re.sub(r'\s+', '', t).replace('’', "'")
        if norm(s['unit_name']) not in norm(text) or reader.metadata.author != s['unit_name']:
            errors.append(f'PDF must use the full unit name: {pdf}')
        if norm(s[p['lang']]['updated_date']) not in norm(text):
            errors.append(f'PDF update date missing: {pdf}')
        if norm(p['title']) not in norm(text):
            errors.append(f'PDF title missing: {pdf}')
        for token in MD.parse(p['body']):
            if token.type == 'inline':
                plain = ''.join(t.content for t in token.children if t.type in {'text', 'code_inline'})
                if norm(plain) not in norm(text):
                    errors.append(f'PDF content missing or clipped: {pdf}: {plain[:50]}')
    cache = {path.resolve(): BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser') for path in pages}
    for path, soup in cache.items():
        if not soup.find('h1'):
            errors.append(f'Page lacks H1: {path}')
        footer = soup.select_one('.site-footer')
        stamp = soup.select_one('.site-footer time')
        if not footer or s['unit_name'] not in footer.get_text(' ', strip=True):
            errors.append(f'Footer must use the full unit name: {path}')
        if not stamp or stamp.get('datetime') != s['last_updated']:
            errors.append(f'Missing or incorrect update date: {path}')
        if re.search(r'\bTSCN\b', soup.get_text(' ', strip=True)):
            errors.append(f'Use the full unit name instead of its abbreviation: {path}')
        for tag in soup.select('[href], [src]'):
            value = tag.get('href') or tag.get('src')
            if not value or value.startswith(('data:', 'mailto:', 'tel:')): continue
            url = urlsplit(value)
            if url.scheme or url.netloc: continue
            target = (OUT / unquote(url.path).lstrip('/') if url.path.startswith('/') else path.parent / unquote(url.path)) if url.path else path
            target = target.resolve()
            if tag.name == 'a' and (url.path.startswith('/') or target.is_dir()):
                errors.append(f'Link must target a relative file, not a directory: {path.relative_to(OUT)} -> {value}')
            if target.is_dir(): target = target / 'index.html'
            if not target.is_relative_to(OUT.resolve()) or not target.is_file():
                errors.append(f'Broken internal reference: {path.relative_to(OUT)} -> {value}')
            elif url.fragment and target.suffix == '.html':
                doc = cache.get(target)
                if doc and not doc.find(id=unquote(url.fragment)) and not doc.find(attrs={'name': unquote(url.fragment)}):
                    errors.append(f'Broken anchor: {path.relative_to(OUT)} -> {value}')
    # Public output is an allowlist, not a copy of the repository.
    root_files = {'index.html','student-projects.html','jobs.html','about.html','expectations.html','funding.html','apply.html','programmes.html','404.html','CNAME','robots.txt','sitemap.xml','search.json','.nojekyll'}
    expected_project_files = {f'projects/{p["slug"]}/{name}' for p in ps for name in ('index.html','advert.pdf')}
    assets = {'assets/tscn-logo.png','assets/favicon.png','assets/social-preview.png','assets/site.css','assets/search.js'}
    for path in OUT.rglob('*'):
        if path.is_symlink(): errors.append(f'Symlink in public output: {path}')
        if not path.is_file(): continue
        rel = path.relative_to(OUT).as_posix()
        allowed = rel in root_files | assets | expected_project_files or (rel.startswith('site_libs/') and path.suffix in {'.js','.css','.woff','.woff2','.ttf','.map'})
        if PRIVATE.search(rel) or not allowed:
            errors.append(f'Unexpected public file: {rel}')
    if not (OUT / 'CNAME').is_file() or (OUT / 'CNAME').read_text().strip() != 'join.tscnlab.org':
        errors.append('Missing or incorrect custom domain')
    catalogue = cache.get((OUT / 'student-projects.html').resolve())
    if catalogue:
        cards = catalogue.select('.project-card')
        targets = ['/' + c.select_one('h3 a')['href'].lstrip('./') for c in cards]
        expected = {f'/projects/{p["slug"]}/index.html' for p in ps if p['status'] == 'open'}
        if len(targets) != len(set(targets)) or set(targets) != expected:
            errors.append('Catalogue must list each open project exactly once')
    if errors: raise ValueError('\n'.join(errors))
    print(f'PASS: {len(ps)} HTML/PDF pairs, single-page A4, complete PDF text, {len(pages)} HTML pages, internal links, catalogue and public-file allowlist.')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare','pdfs','validate','finish','check-output','build'])
    args = parser.parse_args()
    if args.command == 'prepare': prepare()
    elif args.command == 'pdfs': pdfs()
    elif args.command == 'validate':
        ps = projects(); ensure_logo(); check_tracked_private(); print(f'PASS: {len(ps)} project metadata records and canonical logo.')
    elif args.command == 'check-output': validate_output()
    elif args.command == 'finish':
        portable_links(); pdfs(); (OUT / '.nojekyll').touch(); validate_output()
    elif args.command == 'build':
        # Clean output avoids retaining deleted opportunities or stale private assets.
        import shutil
        if OUT.exists(): shutil.rmtree(OUT)
        prepare()  # Quarto discovers include files before running its pre-render hook.
        subprocess.run(['quarto','render'], cwd=ROOT, check=True)


if __name__ == '__main__':
    try: main()
    except (ValueError, RuntimeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr); sys.exit(1)
