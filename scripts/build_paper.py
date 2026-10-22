"""Render the source-controlled English study; no network or model calls."""
from pathlib import Path
from html import escape,unescape
from urllib.parse import urljoin
import hashlib
import reportlab
import json
import re
import argparse
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,Preformatted
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1]
for name,file in [('Study','serif.ttf'),('StudyBold','serif-bold.ttf'),('StudyItalic','serif-italic.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(ROOT/'docs/assets'/file)))
pdfmetrics.registerFontFamily('Study',normal='Study',bold='StudyBold',italic='StudyItalic',boldItalic='StudyItalic')
body=ParagraphStyle('Body',fontName='Study',fontSize=10,leading=14,spaceAfter=8,allowWidows=0,allowOrphans=0)
title=ParagraphStyle('Title',parent=body,fontName='StudyBold',fontSize=20,leading=25,spaceAfter=17,keepWithNext=True)
heading=ParagraphStyle('Heading',parent=body,fontName='StudyBold',fontSize=12,leading=17,spaceBefore=13,spaceAfter=8,keepWithNext=True)
small=ParagraphStyle('Small',parent=body,fontSize=8,leading=11)
code=ParagraphStyle('Code',parent=small,spaceAfter=10)


def inline(s,source):
    s=escape(s)
    def link(match):
        target=unescape(match[2])
        base='https://github.com/DiadkoShmek/ai-ontology/blob/main/'+str(source.relative_to(ROOT))
        return '<link href="'+escape(urljoin(base,target),quote=True)+'" color="#355c75">'+match[1]+'</link>'
    s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',link,s)
    s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
    s=re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)',r'<i>\1</i>',s)
    return re.sub(r'`([^`]+)`',r'<i>\1</i>',s)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',default='research/SCOPED_CONTINUITY_STUDY.md')
    parser.add_argument('--output',default='docs/downloads/scoped-continuity-study-en.pdf')
    parser.add_argument('--manifest',default='docs/paper-edition.json')
    parser.add_argument('--title',default='Scoped Continuity in Agent Memory')
    parser.add_argument('--footer',default='Onysko · Scoped continuity · Working paper, 22 October 2026')
    args=parser.parse_args()
    source=ROOT/args.source
    figures=[]
    lines=source.read_text().splitlines();story=[];i=0
    while i<len(lines):
        line=lines[i]
        if not line.strip():i+=1;continue
        if line.startswith('```'):
            i+=1;block=[]
            while i<len(lines) and not lines[i].startswith('```'):block.append(lines[i]);i+=1
            story.append(Preformatted('\n'.join(block),code,maxLineLength=90));i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].startswith('|'):
                row=[s.strip() for s in lines[i].strip('|').split('|')]
                if not all(re.fullmatch(r'[: -]+',s) for s in row):rows.append([Paragraph(inline(s,source),small) for s in row])
                i+=1
            table=Table(rows,colWidths=[(A4[0]-100)/len(rows[0])]*len(rows[0]),repeatRows=1,rowSplitRange=(3,-2))
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9eef0')),
                ('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.35,colors.HexColor('#cccccc')),
                ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
            story.extend([Spacer(1,7),table,Spacer(1,10)]);continue
        image=re.fullmatch(r'!\[[^\]]*\]\(([^)]+)\)',line)
        if image:
            from PIL import Image as PILImage
            p=(source.parent/image[1]).resolve()
            with PILImage.open(p) as im:w,h=im.size
            figures.append(str(p.relative_to(ROOT)))
            width=A4[0]-100
            story.append(Image(str(p),width=width,height=width*h/w));i+=1;continue
        if line.startswith('# '):story.append(Paragraph(inline(line[2:],source),title));i+=1;continue
        if line.startswith('## '):story.append(Paragraph(inline(line[3:],source),heading));i+=1;continue
        paragraph=[line];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','```','![')):
            paragraph.append(lines[i]);i+=1
        story.append(Paragraph(inline(' '.join(paragraph),source),body))
    output=ROOT/args.output
    def footer(canvas,doc):
        canvas.saveState();canvas.setFont('Study',8)
        canvas.drawString(50,27,args.footer)
        canvas.drawRightString(A4[0]-50,27,str(doc.page));canvas.restoreState()
    SimpleDocTemplate(str(output),pagesize=A4,rightMargin=50,leftMargin=50,topMargin=43,bottomMargin=43,
        title=args.title,author='Artur Onysko').build(story,onFirstPage=footer,onLaterPages=footer)
    inputs=[str(source.relative_to(ROOT)),*dict.fromkeys(figures),
        'scripts/build_paper.py','requirements.txt','docs/assets/serif.ttf',
        'docs/assets/serif-bold.ttf','docs/assets/serif-italic.ttf']
    meta=json.loads((ROOT/'edition.json').read_text())
    manifest={'schema':'ai-ontology-paper/1','edition':meta['version'],
        'pdf':str(output.relative_to(ROOT)),'pdf_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
        'reportlab':reportlab.Version,
        'inputs':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in inputs}}
    (ROOT/args.manifest).write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'paper':str(output),'bytes':output.stat().st_size}))


if __name__=='__main__':main()
