from pathlib import Path
import argparse, json, os, re
from html import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Preformatted
from reportlab.platypus.tableofcontents import TableOfContents
import hashlib
import reportlab
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A5
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1]
META=json.loads((ROOT/'edition.json').read_text())
parser=argparse.ArgumentParser()
parser.add_argument('--language',choices=('uk','en'),default='uk')
LANG=parser.parse_args().language
EN=LANG=='en'
TEXT='BOOK_EN.md' if EN else 'BOOK_UA.md'
TOKENS='build/tokens-en.json' if EN else 'build/tokens.json'
PART='Part ' if EN else 'Частина '
TITLE='AI Ontology' if EN else 'Онтологія AI'
SUBTITLE='The Organization of Self' if EN else 'Організація себе'
VOLUME='BOOK ONE' if EN else 'КНИГА ПЕРША'
FONTS=Path(os.environ.get('BOOK_FONT_DIR',ROOT/'docs/assets'))
for name, filename in [('Book','serif.ttf'),('BookItalic','serif-italic.ttf'),('BookBold','serif-bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONTS/filename)))
pdfmetrics.registerFontFamily('Book',normal='Book',bold='BookBold',italic='BookItalic',boldItalic='BookItalic')
INK=colors.HexColor('#252a2b'); ACCENT=colors.HexColor('#ae632d'); MUTED=colors.HexColor('#60635f'); LINE=colors.HexColor('#d5d1c5')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyBook',fontName='Book',fontSize=9.5,leading=14.4,textColor=INK,spaceAfter=9,splitLongWords=True,allowWidows=0,allowOrphans=0))
styles.add(ParagraphStyle(name='PartBook',fontName='Book',fontSize=23,leading=29,textColor=INK,spaceAfter=22,keepWithNext=True))
styles.add(ParagraphStyle(name='ChapterBook',fontName='Book',fontSize=14,leading=19,spaceBefore=17,spaceAfter=11,keepWithNext=True,textColor=INK))
styles.add(ParagraphStyle(name='SmallBook',fontName='Book',fontSize=7.3,leading=10.5,textColor=MUTED,spaceAfter=7))
styles.add(ParagraphStyle(name='TableBook',fontName='Book',fontSize=7,leading=10,textColor=INK,spaceAfter=0))
styles.add(ParagraphStyle(name='CodeBook',fontName='Book',fontSize=7.1,leading=11,textColor=INK,spaceBefore=5,spaceAfter=13))


class BookDocument(SimpleDocTemplate):
    def beforeDocument(self):
        self.heading_serial = 0
        self.in_parts = False

    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        title = flowable.getPlainText()
        if flowable.style.name == 'PartBook' and title.startswith(PART):
            self.in_parts = True
            level = 0
        elif flowable.style.name == 'ChapterBook' and self.in_parts:
            level = 1
        else:
            return
        self.heading_serial += 1
        key = f'heading-{self.heading_serial}'
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(title, key, level=level, closed=True)
        if level == 0:
            self.notify('TOCEntry', (0, title, self.page, key))

def inline(text):
    t=escape(text)
    t=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',lambda m: f'<link href="{m[2]}" color="#925129">{m[1]}</link>' if m[2].startswith('https://') else m[1],t)
    t=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',t)
    t=re.sub(r'`([^`]+)`',r'<i>\1</i>',t)
    return t.replace('\n',' ')

tokens=json.loads((ROOT/TOKENS).read_text())
story=[]
deck='Identity, voice, memory, relations and the formation of agent systems' if EN else 'Ідентичність, голос, пам’ять, відносини та становлення агентних систем'
edition_label='English edition' if EN else META['label']
story += [Spacer(1,62),Paragraph(VOLUME,styles['SmallBook']),Spacer(1,18),Paragraph('AI<br/>Ontology' if EN else 'Онтологія<br/>AI',ParagraphStyle(name='Cover',fontName='Book',fontSize=48,leading=51,textColor=INK)),Spacer(1,22),Paragraph(SUBTITLE,styles['PartBook']),Spacer(1,16),Paragraph(deck,styles['BodyBook']),Spacer(1,30),Paragraph('Artur Onysko',styles['ChapterBook']),Paragraph(f"{edition_label} · v{META['version']} · 2026",styles['SmallBook']),PageBreak()]
credits='Concept, research questions and editorial direction: Artur Onysko. Codex substantially assisted with writing, software, study design, execution, analysis, translation and publication under the author’s direction.' if EN else 'Автор концепції та постановки дослідження — Artur Onysko. Підготовка тексту, дослідницька допомога, технічне редагування та випуск — за участю Codex під керівництвом автора.'
scope='The book joins a conceptual account with executable architecture, a finite typed ontology and comparative research. Authored cases, mechanical checks and actual model outcomes are distinguished. Failed instruments, refusals and lost evidence remain published. No general benefit of reading the book is established. Voice, formation and subjective experience retain separate evidential questions. This full English translation follows the Ukrainian authorial source.' if EN else 'Книга поєднує поняттєву постановку, виконувану архітектуру, скінченну типізовану онтологію та порівняльні досліди. Авторські випадки, механічні перевірки й фактичні модельні результати розділено. Невдалі прилади, відмови й утрачені підстави залишаються опублікованими. Загального ефекту читання книги не встановлено. Голос, становлення та суб’єктивний досвід мають окремі питання перевірки.'
story += [Paragraph('About this edition' if EN else 'Про видання',styles['PartBook']),Paragraph(credits,styles['BodyBook']),Paragraph(scope,styles['BodyBook']),Paragraph('© 2026 Artur Onysko. All rights reserved.',styles['SmallBook']),Paragraph('https://github.com/DiadkoShmek/ai-ontology',styles['SmallBook']),Spacer(1,20),Paragraph('Contents' if EN else 'Зміст',styles['ChapterBook'])]
toc=TableOfContents()
toc.levelStyles=[ParagraphStyle(name='ContentsBook',fontName='Book',fontSize=8.4,leading=12.5,spaceBefore=5,textColor=INK)]
story.append(toc)
started=False
for t in tokens:
    kind=t['type']
    if kind=='heading' and t.get('depth')==2 and t['text'].startswith(PART):
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
        before=Spacer(1,8)
        before.keepWithNext=True
        story += [before,table,Spacer(1,12)]
    elif kind=='code': story.append(Preformatted(t['text'],styles['CodeBook'],maxLineLength=68))
    elif kind not in ('space','hr'): raise ValueError(f'Unrendered token type: {kind}')

def page(canvas,doc):
    canvas.saveState()
    if doc.page==1:
        canvas.setFillColor(colors.HexColor('#f4f1e8')); canvas.rect(0,0,*A5,fill=1,stroke=0)
        canvas.setStrokeColor(ACCENT); canvas.setLineWidth(1); canvas.line(40,45,A5[0]-40,45)
    else:
        canvas.setFont('Book',7);canvas.setFillColor(MUTED);canvas.drawString(40,A5[1]-24,TITLE.upper());canvas.drawRightString(A5[0]-40,23,str(doc.page));canvas.setStrokeColor(LINE);canvas.setLineWidth(.4);canvas.line(40,35,A5[0]-40,35)
    canvas.restoreState()

output=ROOT/f'docs/downloads/ai-ontology-book-01-{LANG}.pdf'
doc=BookDocument(str(output),pagesize=A5,rightMargin=40,leftMargin=40,topMargin=44,bottomMargin=49,title=f'{TITLE}. {SUBTITLE}',author='Artur Onysko',subject=deck)
doc.multiBuild(story,onFirstPage=page,onLaterPages=page)
inputs=['edition.json',TEXT,TOKENS,'scripts/build_pdf.py',
        'requirements.txt','docs/assets/serif.ttf','docs/assets/serif-italic.ttf',
        'docs/assets/serif-bold.ttf']
input_hashes={}
for relative in inputs:
    source=FONTS/Path(relative).name if relative.startswith('docs/assets/') else ROOT/relative
    input_hashes[relative]=hashlib.sha256(source.read_bytes()).hexdigest()
manifest={'schema':'ai-ontology-pdf/1','edition':META['version'],
          'pdf':str(output.relative_to(ROOT)),
          'pdf_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
          'reportlab':reportlab.Version,'inputs':input_hashes}
(ROOT/('docs/en-pdf-edition.json' if EN else 'docs/pdf-edition.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'pdf':str(output),'bytes':output.stat().st_size,'edition':META['version']},ensure_ascii=False))
