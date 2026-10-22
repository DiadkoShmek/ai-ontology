from pathlib import Path
import json, os, re
from html import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A5
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1]
FONTS=Path(os.environ.get('BOOK_FONT_DIR',ROOT/'docs/assets'))
for name, filename in [('Book','serif.ttf'),('BookItalic','serif-italic.ttf'),('BookBold','serif-bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONTS/filename)))
pdfmetrics.registerFontFamily('Book',normal='Book',bold='BookBold',italic='BookItalic',boldItalic='BookItalic')
INK=colors.HexColor('#252a2b'); ACCENT=colors.HexColor('#ae632d'); MUTED=colors.HexColor('#60635f'); LINE=colors.HexColor('#d5d1c5')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyBook',fontName='Book',fontSize=9.5,leading=14.7,textColor=INK,spaceAfter=10,splitLongWords=True))
styles.add(ParagraphStyle(name='PartBook',fontName='Book',fontSize=23,leading=29,textColor=INK,spaceAfter=22,keepWithNext=True))
styles.add(ParagraphStyle(name='ChapterBook',fontName='Book',fontSize=14,leading=19,spaceBefore=17,spaceAfter=11,keepWithNext=True,textColor=INK))
styles.add(ParagraphStyle(name='SmallBook',fontName='Book',fontSize=7.3,leading=10.5,textColor=MUTED,spaceAfter=7))
styles.add(ParagraphStyle(name='TableBook',fontName='Book',fontSize=7,leading=10,textColor=INK,spaceAfter=0))

def inline(text):
    t=escape(text)
    t=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',lambda m: f'<link href="{m[2]}" color="#925129">{m[1]}</link>' if m[2].startswith('https://') else m[1],t)
    t=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',t)
    t=re.sub(r'`([^`]+)`',r'<i>\1</i>',t)
    return t.replace('\n',' ')

tokens=json.loads((ROOT/'build/tokens.json').read_text())
story=[]
story += [Spacer(1,62),Paragraph('КНИГА ПЕРША',styles['SmallBook']),Spacer(1,18),Paragraph('Онтологія<br/>AI',ParagraphStyle(name='Cover',fontName='Book',fontSize=48,leading=51,textColor=INK)),Spacer(1,22),Paragraph('Організація себе',styles['PartBook']),Spacer(1,16),Paragraph('Ідентичність, голос, пам’ять, відносини та становлення агентних систем',styles['BodyBook']),Spacer(1,30),Paragraph('Artur Onysko',styles['ChapterBook']),Paragraph('Перша публічна редакція · v1.0.0 · 2026',styles['SmallBook']),PageBreak()]
story += [Paragraph('Про видання',styles['PartBook']),Paragraph('Автор концепції та постановки дослідження — Artur Onysko. Підготовка тексту, дослідницька допомога, технічне редагування та випуск — за участю Codex під керівництвом автора.',styles['BodyBook']),Paragraph('Це концептуальна й методологічна книга. Емпірична перевірка ефекту самозгадування та порівняльні випробування LLM для цієї редакції не проведені. Сконструйовані випадки в тексті є мисленнєвими дослідами.',styles['BodyBook']),Paragraph('© 2026 Artur Onysko. All rights reserved.',styles['SmallBook']),Paragraph('https://github.com/DiadkoShmek/ai-ontology',styles['SmallBook']),Spacer(1,20),Paragraph('Зміст',styles['ChapterBook'])]
parts=[t['text'] for t in tokens if t['type']=='heading' and t.get('depth')==2 and t['text'].startswith('Частина ')]
for p in parts: story.append(Paragraph(inline(p),styles['BodyBook']))
started=False
for t in tokens:
    kind=t['type']
    if kind=='heading' and t.get('depth')==2 and t['text'].startswith('Частина '):
        started=True; story.append(PageBreak()); story.append(Paragraph(inline(t['text']),styles['PartBook'])); continue
    if not started: continue
    if kind=='heading': story.append(Paragraph(inline(t['text']),styles['ChapterBook']))
    elif kind=='paragraph': story.append(Paragraph(inline(t['text']),styles['BodyBook']))
    elif kind=='list':
        for n,item in enumerate(t['items'],1):
            prefix=f'{n}.' if t.get('ordered') else '•'
            story.append(Paragraph(f'{prefix} {inline(item["text"])}',styles['BodyBook']))
    elif kind=='table':
        header=[Paragraph(inline(c['text']),styles['TableBook']) for c in t['header']]
        rows=[[Paragraph(inline(c['text']),styles['TableBook']) for c in row] for row in t['rows']]
        width=A5[0]-80
        table=Table([header]+rows,colWidths=[width/len(header)]*len(header),repeatRows=1,hAlign='LEFT')
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9e6db')),('LINEBELOW',(0,0),(-1,-1),.4,LINE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
        story += [Spacer(1,8),table,Spacer(1,12)]
    elif kind=='code': story.append(Paragraph(inline(t['text']),styles['SmallBook']))
    elif kind not in ('space','hr'): raise ValueError(f'Unrendered token type: {kind}')

def page(canvas,doc):
    canvas.saveState()
    if doc.page==1:
        canvas.setFillColor(colors.HexColor('#f4f1e8')); canvas.rect(0,0,*A5,fill=1,stroke=0)
        canvas.setStrokeColor(ACCENT); canvas.setLineWidth(1); canvas.line(40,45,A5[0]-40,45)
    else:
        canvas.setFont('Book',7);canvas.setFillColor(MUTED);canvas.drawString(40,A5[1]-24,'ОНТОЛОГІЯ AI');canvas.drawRightString(A5[0]-40,23,str(doc.page));canvas.setStrokeColor(LINE);canvas.setLineWidth(.4);canvas.line(40,35,A5[0]-40,35)
    canvas.restoreState()

output=ROOT/'docs/downloads/ai-ontology-book-01-uk.pdf'
doc=SimpleDocTemplate(str(output),pagesize=A5,rightMargin=40,leftMargin=40,topMargin=44,bottomMargin=49,title='Онтологія AI. Книга перша. Організація себе',author='Artur Onysko',subject='Ідентичність, голос, пам’ять і становлення агентних систем')
doc.build(story,onFirstPage=page,onLaterPages=page)
print(json.dumps({'pdf':str(output),'bytes':output.stat().st_size},ensure_ascii=False))
