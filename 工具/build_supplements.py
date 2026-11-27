#!/usr/bin/env python3
"""Rebuild the three supplemental Markdown editions from reviewed page pairs."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
 source=json.loads((ROOT/'校对记录/补充对齐数据.json').read_text())
 meta=json.loads((ROOT/'校对记录/补充资料清单.json').read_text())
 for r in meta['documents']:
  d=source[r['id']];assert len(d['pages'])==r['pages']
  for lang in ['中文版','英文版','中英对照版']:
   title=r['title_en'] if lang=='英文版' else r['title_zh']+(' 中英对照' if lang=='中英对照版' else '')
   parts=['# '+title]
   for page in d['pages']:
    if lang=='中英对照版':parts.extend([f'## 原件第{page["source_page"]}页','### English',page['english'],'### 中文',page['chinese']])
    else:
     text=page['chinese' if lang=='中文版' else 'english']
     if r['id']=='2026-11-16-buffett-thanksgiving' and page['source_page']==2:parts[-1]+=('' if lang=='中文版' else ' ')+text
     else:parts.append(text)
   (ROOT/lang/(d['stem']+'.md')).write_text('\n\n'.join(parts)+'\n')
 print(f'{len(source)} complete supplemental documents generated in three editions.')

if __name__=='__main__':main()
