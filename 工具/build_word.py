#!/usr/bin/env python3
"""Build Word reading editions from the adjacent Markdown files."""
import argparse,hashlib,json,re,io
from pathlib import Path
from docx import Document
from docx.enum.section import WD_SECTION_START,WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm,Pt,RGBColor
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
LANGS=['中文版','英文版','中英对照版']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def plain(s):
 s=re.sub(r'<[^>]+>','',s)
 s=re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',s)
 s=s.replace('**','').replace('__','').replace('`','')
 s=re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)',r'\1',s)
 return s.strip()

def style_font(style,size,family='Songti SC'):
 style.font.name=family;style.font.size=Pt(size);style.font.color.rgb=RGBColor(0,0,0)
 rpr=style.element.get_or_add_rPr();fonts=rpr.find(qn('w:rFonts'))
 if fonts is None:fonts=OxmlElement('w:rFonts');rpr.append(fonts)
 for a,v in [('ascii',family),('hAnsi',family),('eastAsia','Songti SC')]:fonts.set(qn('w:'+a),v)
 for key in ['asciiTheme','hAnsiTheme','eastAsiaTheme','cstheme']:fonts.attrib.pop(qn('w:'+key),None)

def section_layout(section,landscape=False):
 section.orientation=WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
 section.page_width=Mm(297 if landscape else 210);section.page_height=Mm(210 if landscape else 297)
 section.top_margin=Mm(17);section.bottom_margin=Mm(17);section.left_margin=Mm(18);section.right_margin=Mm(18)

def add_table(doc,lines):
 rows=[[plain(c) for c in l.strip().split('|')[1:-1]] for l in lines]
 rows=[rows[0]]+rows[2:];cols=len(rows[0]);assert all(len(r)==cols for r in rows)
 table=doc.add_table(rows=0,cols=cols);table.alignment=WD_TABLE_ALIGNMENT.CENTER;table.autofit=False
 width=174
 first=.22 if max((len(r[0]) for r in rows[1:]),default=0)<15 else .37
 weights=([.53,.47] if cols==2 else [first]+[(1-first)/(cols-1)]*(cols-1))
 for c,w in zip(table.columns,weights):c.width=Mm(width*w)
 borders=OxmlElement('w:tblBorders')
 for side in ['top','left','bottom','right','insideH','insideV']:
  node=OxmlElement('w:'+side);node.set(qn('w:val'),'single');node.set(qn('w:sz'),'4');node.set(qn('w:color'),'D9D9D9');borders.append(node)
 table._tbl.tblPr.append(borders)
 margins=OxmlElement('w:tblCellMar')
 for side in ['top','bottom','left','right']:
  node=OxmlElement('w:'+side);node.set(qn('w:w'),'70');node.set(qn('w:type'),'dxa');margins.append(node)
 table._tbl.tblPr.append(margins)
 for i,rowdata in enumerate(rows):
  row=table.add_row();trpr=row._tr.get_or_add_trPr();nosplit=OxmlElement('w:cantSplit');trpr.append(nosplit)
  if i==0:trpr.append(OxmlElement('w:tblHeader'))
  for j,(cell,text) in enumerate(zip(row.cells,rowdata)):
   cell.width=Mm(width*weights[j]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   p=cell.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.LEFT if j==0 else WD_ALIGN_PARAGRAPH.CENTER
   p.paragraph_format.space_before=Pt(1);p.paragraph_format.space_after=Pt(1);p.paragraph_format.line_spacing=1.1
   run=p.add_run(text);run.font.size=Pt(8.5 if cols>=5 else 9)
   if i==0:
    run.bold=True;fill=OxmlElement('w:shd');fill.set(qn('w:fill'),'E8EDF1');cell._tc.get_or_add_tcPr().append(fill)
 doc.add_paragraph().paragraph_format.space_after=Pt(2)

def add_image(doc,path):
 assert path.is_file(),path
 with Image.open(path) as im:
  w,h=im.size;buffer=io.BytesIO();im.convert('RGB').save(buffer,format='PNG');buffer.seek(0)
 width=min(174,239*w/h)
 p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.add_run().add_picture(buffer,width=Mm(width))

def compact_code(lines):
 # Dot leaders are decorative. Remove only columns that are blank in every
 # row, preserving the relative positions of all text and numeric columns.
 lines=[re.sub(r'(?:\.\s*){3,}',lambda m:' '*len(m[0]),line) for line in lines]
 width=max((len(line) for line in lines),default=0)
 blank=''.join('1' if all(i>=len(l) or l[i]==' ' for l in lines) else '0' for i in range(width))
 remove=set()
 for m in re.finditer(r'1{3,}',blank):remove.update(range(m.start()+2,m.end()))
 return [''.join(c for i,c in enumerate(l) if i not in remove).rstrip() for l in lines]

def build(path):
 doc=Document();section_layout(doc.sections[0]);lang=path.parent.name
 for border in list(doc.styles.element.iter(qn('w:pBdr'))):border.getparent().remove(border)
 family='Times New Roman' if lang=='英文版' else 'Songti SC'
 style_font(doc.styles['Normal'],11 if lang=='英文版' else 10.5,family)
 doc.styles['Normal'].paragraph_format.line_spacing=1.2
 doc.styles['Normal'].paragraph_format.space_after=Pt(6)
 # Keep the one-page Chinese donation release and its contact details together.
 if lang=='中文版' and path.stem=='2025-06-27-Buffett-Philanthropy':
  doc.styles['Normal'].paragraph_format.line_spacing=1.15
  doc.styles['Normal'].paragraph_format.space_after=Pt(4)
 for name,size in [('Title',19),('Heading 1',15),('Heading 2',12.5),('Heading 3',11.5)]:
  style_font(doc.styles[name],size,family);doc.styles[name].paragraph_format.keep_with_next=True
 style_font(doc.styles['Quote'],10.5,family)
 for st in ['Title','Heading 1','Heading 2','Heading 3','Quote']:
  doc.styles[st].paragraph_format.space_before=Pt(10 if st!='Title' else 0)
  doc.styles[st].paragraph_format.space_after=Pt(6)
 doc.core_properties.title=path.stem+' '+lang
 doc.core_properties.author='';doc.core_properties.last_modified_by=''
 lines=path.read_text().splitlines();i=0;has_title=False;table_count=0;image_count=0;code_count=0;current_land=False
 while i<len(lines):
  line=lines[i];s=line.strip()
  if not s or s.startswith('<!--'):i+=1;continue
  if s.startswith('```'):
   code=[];i+=1
   while i<len(lines) and not lines[i].strip().startswith('```'):code.append(lines[i]);i+=1
   code_count+=1;code=compact_code(code)
   maxlen=max((len(x) for x in code),default=1);land=maxlen>110
   if land!=current_land:
    section_layout(doc.add_section(WD_SECTION_START.NEW_PAGE),land);current_land=land
   size=min(8.5,(740 if land else 493)/(.61*maxlen))
   for l in code:
    p=doc.add_paragraph();p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1.08
    run=p.add_run(l);run.font.name='Courier New';run.font.size=Pt(size)
   doc.add_paragraph().paragraph_format.space_after=Pt(3)
   i+=1;continue
  if re.fullmatch(r'(?:[-*_]\s*){3,}',s):
   doc.add_paragraph().paragraph_format.space_after=Pt(6);i+=1;continue
  if current_land:
   section_layout(doc.add_section(WD_SECTION_START.NEW_PAGE));current_land=False
  if s.startswith('|'):
   block=[]
   while i<len(lines) and lines[i].strip().startswith('|'):block.append(lines[i]);i+=1
   add_table(doc,block);table_count+=1;continue
  images=re.findall(r'!\[[^\]]*\]\(([^)]+)\)',s)+re.findall(r'<img[^>]+src=["\x27]([^"\x27]+)',s)
  if images:
   for image in images:add_image(doc,(path.parent/image).resolve());image_count+=1
   i+=1;continue
  heading=re.match(r'^(#{1,6})\s+(.+)',s)
  if heading:
   level=len(heading[1]);text=plain(heading[2])
   if level==1 and not has_title:
    doc.add_paragraph(re.sub(r'[｜|：:—]+',' ',text),style='Title');has_title=True
   else:doc.add_paragraph(text,style='Heading '+str(min(level,3)))
   i+=1;continue
  if s.startswith('>'):
   quote=[]
   while i<len(lines) and lines[i].strip().startswith('>'):
    quote.append(plain(re.sub(r'^\s*>\s?','',lines[i])));i+=1
   doc.add_paragraph('\n'.join(quote),style='Quote');continue
  bullet=re.match(r'^([-*]|\d+[.、])\s+(.+)',s)
  text=plain(s)
  if bullet:
   if bullet[1] in ['-','*']:p=doc.add_paragraph(plain(bullet[2]),style='List Bullet')
   else:
    p=doc.add_paragraph(text);p.paragraph_format.left_indent=Mm(4)
  else:
   p=doc.add_paragraph()
   run=p.add_run(text)
   if s.startswith('*') and s.endswith('*') and not s.startswith('**'):run.italic=True
  i+=1
 out=path.with_suffix('.docx');doc.save(out)
 return dict(file=str(out.relative_to(ROOT)),markdown_sha256=sha(path),word_sha256=sha(out),tables=table_count,images=image_count,fixed_width_blocks=code_count,render_status='pending')

def main():
 parser=argparse.ArgumentParser();select=parser.add_mutually_exclusive_group();select.add_argument('--year',type=int);select.add_argument('--stem');select.add_argument('--supplements',action='store_true');parser.add_argument('--language',choices=LANGS);args=parser.parse_args()
 meta_path=ROOT/'校对记录/补充资料清单.json'
 supplementary=json.loads(meta_path.read_text())['documents'] if meta_path.exists() else []
 stems=[r['edition_stem'] for r in supplementary if r.get('edition_stem')]
 records=[]
 for lang in ([args.language] if args.language else LANGS):
  if args.year:paths=[ROOT/lang/f'{args.year}.md']
  elif args.stem:paths=[ROOT/lang/(args.stem+'.md')]
  elif args.supplements:paths=[ROOT/lang/(stem+'.md') for stem in stems]
  else:paths=sorted((ROOT/lang).glob('[0-9][0-9][0-9][0-9].md'))+[ROOT/lang/(stem+'.md') for stem in stems]
  for path in paths:
   record=build(path);records.append(record);print(record['file'],flush=True)
 inventory=ROOT/'校对记录/Word构建清单.json'
 existing=json.loads(inventory.read_text()) if inventory.exists() else []
 merged={r['file']:r for r in existing};merged.update({r['file']:r for r in records})
 inventory.write_text(json.dumps(sorted(merged.values(),key=lambda r:r['file']),ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
