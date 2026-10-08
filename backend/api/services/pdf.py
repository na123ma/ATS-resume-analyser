import io
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether


def export_resume(data):
    regular, bold = 'Helvetica', 'Helvetica-Bold'
    font_dir = Path('/usr/share/fonts/truetype/dejavu')
    if (font_dir / 'DejaVuSans.ttf').exists():
        if 'DejaVu' not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont('DejaVu', str(font_dir / 'DejaVuSans.ttf')))
            pdfmetrics.registerFont(TTFont('DejaVu-Bold', str(font_dir / 'DejaVuSans-Bold.ttf')))
        regular, bold = 'DejaVu', 'DejaVu-Bold'
    out = io.BytesIO()
    compact = data['template'] == 'compact'
    accent = '#1f3b74' if data['template'] == 'modern' else '#17253b'
    body = ParagraphStyle('body', fontName=regular, fontSize=9.5 if compact else 10,
                          leading=13 if compact else 15, spaceAfter=4, splitLongWords=True)
    heading = ParagraphStyle('heading', parent=body, fontName=bold, fontSize=11, textColor=colors.HexColor(accent), spaceBefore=12, spaceAfter=6, keepWithNext=True)
    title = ParagraphStyle('name', parent=body, fontName=bold, fontSize=22, leading=27, spaceAfter=8)
    subtitle = ParagraphStyle('sub', parent=body, fontName=bold, keepWithNext=True)
    doc = SimpleDocTemplate(out, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=36, bottomMargin=36,
                            title=f"{data['full_name']} - Resume", author=data['full_name'])
    story = []
    def p(value, style=body):
        return Paragraph(escape(str(value)).replace('\n', '<br/>'), style)
    story.append(p(data['full_name'] or 'Your name', title))
    contact = ' | '.join(data[k] for k in ['email', 'phone', 'location'] if data[k])
    if contact: story.append(p(contact))
    if data['links']: story.append(p(data['links']))
    if data['summary']:
        story += [p('SUMMARY', heading), p(data['summary'])]
    if data['skills']:
        story += [p('SKILLS', heading), p(', '.join(data['skills']))]
    for section in ['experience', 'projects', 'education']:
        if not data[section]: continue
        story.append(p(section.upper(), heading))
        for entry in data[section]:
            label = ' - '.join(x for x in [entry['title'], entry['organization']] if x)
            if label: story.append(p(label, subtitle))
            meta = ' | '.join(x for x in [' - '.join(x for x in [entry['start'], entry['end']] if x), entry['location']] if x)
            if meta: story.append(p(meta))
            for line in entry['details'].splitlines():
                if line.strip(): story.append(p('- ' + line.strip().lstrip('-• ')))
            story.append(Spacer(1, 3))
    if data['certifications']:
        story.append(p('CERTIFICATIONS', heading))
        story.extend(p('- ' + x) for x in data['certifications'])
    doc.build(story)
    return out.getvalue()
