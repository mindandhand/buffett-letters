#!/usr/bin/env python3
"""Audit cross-edition alignment, Markdown tables and rendered artifact bindings."""
import hashlib,json,re,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
LANGS=['中文版','英文版','中英对照版']

def normalized(text):
 text=re.sub(r'<!--.*?-->','',text,flags=re.S)
 text=re.sub(r'(?m)^#{1,6} ','',text)
 return re.sub(r'\s+','',text)

def body(path):return path.read_text().split('\n',1)[1]

def main():
 annual=json.loads((ROOT/'校对记录/对齐数据.json').read_text())
 meta=json.loads((ROOT/'校对记录/补充资料清单.json').read_text())
 extra=json.loads((ROOT/'校对记录/补充对齐数据.json').read_text())
 rows=[]
 for year,groups in annual.items():
  for lang,key in [('中文版','chinese'),('英文版','english')]:
   expected='\n'.join(g[key] for g in groups)
   # 1983's retained chapter alignment includes the editorial title inside S01.
   if year=='1983' and key=='chinese':expected=expected.replace('# 巴菲特1983年度致股东信｜完整中文译文','',1)
   assert normalized(body(ROOT/lang/f'{year}.md'))==normalized(expected),(year,lang,'alignment drift')
  parts=[f'# 巴菲特{year}年度致股东信 中英对照']
  for i,g in enumerate(groups,1):
   label='原文第'+str(int(g['refs'][0][1:]))+'页' if g['refs'][0].startswith('P') else f'对照段落{i}'
   parts.extend([f'## {label}','### English',g['english'],'### 中文',g['chinese']])
  assert normalized((ROOT/'中英对照版'/f'{year}.md').read_text())==normalized('\n\n'.join(parts)),year
  rows.append(dict(id=year,alignment_groups=len(groups),three_edition_alignment='passed'))
 for record in meta['documents']:
  aligned=extra[record['id']];assert aligned['source_sha256']==sha(ROOT/record['source_file'])
  assert len(aligned['pages'])==record['pages'] and [p['source_page'] for p in aligned['pages']]==list(range(1,record['pages']+1))
  stem=record['edition_stem']
  for lang,key in [('中文版','chinese'),('英文版','english')]:
   assert normalized(body(ROOT/lang/(stem+'.md')))==normalized('\n'.join(p[key] for p in aligned['pages'])),(record['id'],lang)
  parts=['# '+record['title_zh']+' 中英对照']
  for p in aligned['pages']:parts.extend([f'## 原件第{p["source_page"]}页','### English',p['english'],'### 中文',p['chinese']])
  assert normalized((ROOT/'中英对照版'/(stem+'.md')).read_text())==normalized('\n\n'.join(parts)),stem
  rows.append(dict(id=record['id'],alignment_pages=len(aligned['pages']),three_edition_alignment='passed'))
 table_count=0
 for row in rows:
  stem=row['id'] if row['id'] in annual else extra[row['id']]['stem']
  for lang in LANGS:
   path=ROOT/lang/(stem+'.md')
   for block in re.findall(r'(?:^\|.*\n)+',path.read_text(),re.M):
    lines=block.rstrip().splitlines();widths={len(line.split('|')[1:-1]) for line in lines}
    assert len(lines)>=3 and len(widths)==1,(str(path),'table width')
    assert all(re.fullmatch(r'\s*:?-{3,}:?\s*',c) for c in lines[1].split('|')[1:-1]),(str(path),'table separator')
    if lang=='中文版':table_count+=1
 render=json.loads((ROOT/'校对记录/Word排版检查.json').read_text());build=json.loads((ROOT/'校对记录/Word构建清单.json').read_text());bmap={r['file']:r for r in build}
 assert len(render['documents_checked'])==165 and len(bmap)==165
 for r in render['documents_checked']:
  p=ROOT/r['file'];b=bmap[r['file']]
  assert sha(p)==r['word_sha256']==b['word_sha256'] and sha(p.with_suffix('.md'))==b['markdown_sha256'],r['file']
  assert not r['flags'] and r['pages']==b['rendered_pages'],r['file']
  with zipfile.ZipFile(p) as z:
   assert not any(n.startswith('word/embeddings/') or 'vbaProject' in n for n in z.namelist()),r['file']
   xml=z.read('word/document.xml').decode()
   assert '<w:ins ' not in xml and '<w:del ' not in xml,r['file']
 report=dict(documents=len(rows),annual_documents=len(annual),supplemental_documents=len(meta['documents']),annual_alignment_groups=sum(map(len,annual.values())),supplemental_source_pages=sum(r['pages'] for r in meta['documents']),chinese_markdown_tables=table_count,alignment_check='passed (whitespace and heading markup ignored; body text retained)',markdown_table_structure='passed',word_render_hash_binding='passed',word_markdown_hash_binding='passed',word_files=len(bmap),rendered_word_pages=sum(r['pages'] for r in render['documents_checked']),tracked_changes_macros_embedded_objects='none found',semantic_review_scope='Automated structural checks do not prove sentence meaning. See 总体审查报告.md for semantic sampling and inherited reviews.',records=rows)
 (ROOT/'校对记录/总体检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(f"{len(rows)} documents: three-edition alignment passed; {table_count} Chinese tables structurally valid; 165 Word artifacts bound to reviewed Markdown and render hashes.")

if __name__=='__main__':main()
