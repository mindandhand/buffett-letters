#!/usr/bin/env python3
"""Assemble reviewed alignment groups; does not infer alignment or translate."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'校对记录/对齐数据.json').read_text())
for year,groups in data.items():
 out=[f'# 巴菲特{year}年度致股东信 中英对照']
 for i,g in enumerate(groups,1):
  label='原文第'+str(int(g['refs'][0][1:]))+'页' if g['refs'][0].startswith('P') else f'对照段落{i}'
  out.extend([f'## {label}','### English',g['english'],'### 中文',g['chinese']])
 (ROOT/'中英对照版'/f'{year}.md').write_text('\n\n'.join(out)+'\n')
print('48 bilingual Markdown editions generated.')
