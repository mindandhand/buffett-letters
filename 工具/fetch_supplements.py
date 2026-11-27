#!/usr/bin/env python3
"""Restore missing registered original PDFs; never infer publication or translate."""
import hashlib,json
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[1]
sha=lambda data:hashlib.sha256(data).hexdigest()

def main():
 manifest=json.loads((ROOT/'校对记录/补充资料清单.json').read_text())
 for r in manifest['documents']:
  url=urlparse(r['url'])
  assert url.scheme=='https' and url.hostname in ['www.berkshirehathaway.com','berkshirehathaway.com']
  target=(ROOT/r['source_file']).resolve();assert target.is_relative_to(ROOT)
  if target.exists():
   assert sha(target.read_bytes())==r['sha256'],f'Existing source differs from reviewed hash: {target.name}'
   print('Verified '+target.name);continue
  request=Request(r['url'],headers={'User-Agent':'Buffett-Letters-Source-Archive/1.0'})
  with urlopen(request,timeout=45) as response:payload=response.read()
  assert payload.startswith(b'%PDF-') and sha(payload)==r['sha256'],f'Remote source changed; review before replacing: {target.name}'
  target.parent.mkdir(parents=True,exist_ok=True);temporary=target.with_suffix('.pdf.tmp');temporary.write_bytes(payload);temporary.replace(target)
  print('Downloaded '+target.name)
 print('Registered source PDFs verified. Translation status is unchanged.')

if __name__=='__main__':main()
