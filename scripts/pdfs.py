"""Readable one-page A4 adverts, using exactly the Markdown body used by Quarto."""
from __future__ import annotations

from html import escape
from pathlib import Path

import reportlab
from markdown_it import MarkdownIt
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Spacer

INK = colors.HexColor('#073b4b')
TEXT = colors.HexColor('#293e45')
MUTED = colors.HexColor('#54686e')
LINE = colors.HexColor('#cedad6')
FONT_DIR = Path(reportlab.__file__).parent / 'fonts'
for name, filename in [('TSCN', 'Vera.ttf'), ('TSCN-Bold', 'VeraBd.ttf'), ('TSCN-Italic', 'VeraIt.ttf'), ('TSCN-BoldItalic', 'VeraBI.ttf')]:
    if name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / filename)))
pdfmetrics.registerFontFamily('TSCN', normal='TSCN', bold='TSCN-Bold', italic='TSCN-Italic', boldItalic='TSCN-BoldItalic')


def style(name='body', **kwargs):
    base = dict(fontName='TSCN', fontSize=10.2, leading=13.8, textColor=TEXT, alignment=TA_LEFT, spaceAfter=7)
    base.update(kwargs)
    return ParagraphStyle(name, **base)


def inline(tokens):
    result = []
    for token in tokens or []:
        if token.type in {'text','code_inline'}: result.append(escape(token.content))
        elif token.type == 'softbreak': result.append(' ')
        elif token.type == 'strong_open': result.append('<b>')
        elif token.type == 'strong_close': result.append('</b>')
        elif token.type == 'em_open': result.append('<i>')
        elif token.type == 'em_close': result.append('</i>')
        elif token.type == 'link_open': result.append(f'<a href="{escape(token.attrGet("href"), quote=True)}" color="#073b4b">')
        elif token.type == 'link_close': result.append('</a>')
        else: raise ValueError(f'Unsupported PDF inline token: {token.type}')
    return ''.join(result)


def body_flow(body):
    flow = []; heading = False; bullet = False
    for token in MarkdownIt('commonmark').parse(body):
        if token.type == 'heading_open': heading = True
        elif token.type == 'heading_close': heading = False
        elif token.type == 'list_item_open': bullet = True
        elif token.type == 'list_item_close': bullet = False
        elif token.type == 'inline':
            if heading:
                if flow: flow.append(Spacer(1, 4))
                flow.append(Paragraph(inline(token.children), style('heading', fontName='TSCN-Bold', fontSize=10.5, leading=14, textColor=INK, spaceAfter=5)))
            else:
                flow.append(Paragraph(inline(token.children), style(leftIndent=9 if bullet else 0, bulletIndent=0, spaceAfter=5 if bullet else 7), bulletText='•' if bullet else None))
    return flow


def draw_flow(c, flow, x, top, width, bottom, label):
    measured = [(item, item.wrap(width, 10000)[1]) for item in flow]
    height = sum(h + item.getSpaceAfter() for item, h in measured)
    if top - height < bottom:
        raise ValueError(f'{label}: content exceeds its A4 region by {bottom - (top - height):.1f} pt. Shorten the QMD or shared copy; font size is not reduced.')
    y = top
    for item, h in measured:
        item.drawOn(c, x, y - h); y -= h + item.getSpaceAfter()
    return y


def render_pdf(p, shared, logo, target):
    width, height = A4
    margin = 17 * mm
    usable = width - 2 * margin
    t = shared[p['lang']]; de = p['lang'] == 'de'
    c = canvas.Canvas(str(target), pagesize=A4, invariant=1, pageCompression=1)
    c.setTitle(p['title']); c.setAuthor(shared['unit_name']); c.setSubject(p['subtitle'])
    logo_width = 90 * mm; logo_height = logo_width * 1451 / 7660
    c.drawImage(str(logo), margin, height - margin - logo_height, width=logo_width, height=logo_height, mask='auto')
    top = height - margin - logo_height - 16
    intro = [Paragraph(escape(t['label']).upper(), style(fontSize=8, leading=11, textColor=MUTED, spaceAfter=9))]
    title_size = 21 if len(p['title']) < 70 else 18.5
    intro.append(Paragraph(escape(p['title']), style(fontName='TSCN-Bold', fontSize=title_size, leading=title_size * 1.18, textColor=INK, spaceAfter=8)))
    intro.append(Paragraph(escape(p['subtitle']), style(fontSize=10.6, leading=14.4, textColor=MUTED, spaceAfter=11)))
    labels = {"Master's thesis":'Masterarbeit','Research internship':'Forschungspraktikum','Erasmus+ research placement':'Erasmus+ Forschungsaufenthalt','Engineering project':'Ingenieurprojekt'}
    locations = ' / '.join('München' if de and loc == 'Munich' else loc for loc in p['location'])
    formats = ' · '.join(labels[f] if de else f for f in p['formats'])
    metadata = f'{locations} · {"Deutsch" if de else "English"} · {formats}'
    intro.append(Paragraph(escape(metadata), style(fontSize=8.3, leading=11.8, textColor=MUTED, spaceAfter=0)))
    y = draw_flow(c, intro, margin, top, usable, 400, p['slug'] + ' title')
    c.setStrokeColor(LINE); c.setLineWidth(.6); c.line(margin, y-13, width-margin, y-13)
    top = y - 29
    col_gap = 19
    side_width = 145
    main_width = usable - side_width - col_gap
    bottom = 170
    draw_flow(c, body_flow(p['body']), margin, top, main_width, bottom, p['slug'] + ' body')
    aside = []
    for heading, text in [(t['backgrounds'], ' · '.join(p['backgrounds'])), (t['expectations_title'], t['expectations_short']), (t['funding_title'], t['funding_short'])]:
        aside.append(Paragraph(escape(heading), style(fontName='TSCN-Bold', fontSize=9, leading=12, textColor=INK, spaceAfter=5)))
        aside.append(Paragraph(escape(text), style(fontSize=9, leading=12.5, spaceAfter=10)))
    aside.append(Paragraph(escape(t['fit_note']), style(fontSize=8, leading=11, textColor=MUTED, spaceAfter=0)))
    draw_flow(c, aside, margin+main_width+col_gap, top, side_width, bottom, p['slug'] + ' sidebar')
    c.line(margin, 157, width-margin, 157)
    status = p['status']
    heading = t['apply_title'] if status == 'open' else (t['paused'] if status == 'paused' else t['closed'])
    app = [Paragraph(escape(heading), style(fontName='TSCN-Bold', fontSize=10, leading=13, textColor=INK, spaceAfter=5)), Paragraph(escape(t['application_short']), style(fontSize=9, leading=12, spaceAfter=5))]
    contact = f'München' if de else 'Munich'
    contacts = f'{contact}: <a href="mailto:{shared["contacts"]["Munich"]}">{shared["contacts"]["Munich"]}</a><br/>Tübingen: <a href="mailto:{shared["contacts"]["Tübingen"]}">{shared["contacts"]["Tübingen"]}</a>'
    app.append(Paragraph(contacts, style(fontSize=8.3, leading=11.5, spaceAfter=0)))
    draw_flow(c, app, margin, 144, usable, 57, p['slug'] + ' application')
    url = shared['site_url'] + '/projects/' + p['slug'] + '/'
    footer = [Paragraph(escape(t['about_short']), style(fontSize=7.3, leading=9.5, textColor=MUTED, spaceAfter=3)), Paragraph(f'<a href="{url}">{escape(url.removeprefix("https://"))}</a> · <a href="{shared["mission_url"]}">{"Leitbild" if de else "Mission statement"}</a> · {escape(t["updated_label"])}: {escape(t["updated_date"])}', style(fontSize=7.3, leading=9.5, textColor=INK, spaceAfter=0))]
    draw_flow(c, footer, margin, 48, usable, 13, p['slug'] + ' footer')
    c.showPage(); c.save()
