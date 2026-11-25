#!/usr/bin/env python3
"""Check every edition, source hash, local link and Word text preservation."""
import collections,hashlib,json,re,zipfile
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree as ET
from build_word import plain
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def text_md(t):
 t=re.sub(r'!\[[^\]]*\]\([^)]+\)','',t)
 t=re.sub(r'<img[^>]+>','',t)
 t=re.sub(r'<!--.*?-->','',t,flags=re.S)
 t=re.sub(r'(?m)^```(?:text)?\s*$','',t)
 return plain(t)

def nums(t):return re.findall(r'\d+(?:[.,]\d+)*',t)
def cjk(t):return ''.join(re.findall(r'[\u3400-\u9fff]',t))

def main():
 records=json.loads((ROOT/'校对记录/来源清单.json').read_text());results=[]
 for r in records:
  assert sha(ROOT/r['source_file'])==r['source_sha256']
  year=r['year']
  for lang in ['中文版','英文版','中英对照版']:
   md=ROOT/lang/f'{year}.md';word=md.with_suffix('.docx');assert md.is_file() and word.is_file()
   text=md.read_text();assert not re.search(r'@@|\ufffd|/Users/|TODO',text)
   expected=text_md(text)
   with zipfile.ZipFile(word) as z:
    assert z.testzip() is None
    root=ET.fromstring(z.read('word/document.xml'))
    actual='\n'.join(''.join(n.itertext()) for n in root.findall('.//w:t',NS))
    # Text nodes are in document order, including native table cells.
    assert nums(expected)==nums(actual),(lang,year,'numeric sequence')
    assert cjk(expected)==cjk(actual),(lang,year,'Chinese character sequence')
    en_actual=re.findall(r'[A-Za-z]+',actual)
    assert re.findall(r'[A-Za-z]+',expected)==en_actual,(lang,year,'English word sequence')
   results.append(dict(year=year,language=lang,markdown_sha256=sha(md),word_sha256=sha(word),numeric_sequence='passed',chinese_character_sequence='passed',english_word_sequence='passed'))
 for md in ROOT.rglob('*.md'):
  for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',md.read_text()):
   if link.startswith(('https:','http:','mailto:','#')):continue
   target=unquote(link.split('#',1)[0]);assert (md.parent/target).exists(),(str(md),link)
 assert len(results)==144
 report=dict(years=48,markdown_files=144,word_files=144,original_files=48,source_hashes='passed',local_markdown_links='passed',word_text_preservation='passed',editions=results)
 (ROOT/'校对记录/项目检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print('48 years / 144 Markdown / 144 Word / 48 originals: source hashes, links and Word text checks passed.')

if __name__=='__main__':main()
