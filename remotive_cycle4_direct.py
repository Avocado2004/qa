import urllib.request,time,json,re
from pathlib import Path
O=Path('/opt/data/results/vac-2026-09-24-source-07-cycle-4');R=O/'raw'; UA='Mozilla/5.0'
cards={
'bvu':('https://remotive.com/remote/jobs/qa/software-tester-5925120',5925120),
'1komma5':('https://remotive.com/remote/jobs/qa/senior-qa-engineer-ai-driven-testing-5980080',5980080),
'lemonio':('https://remotive.com/remote/jobs/qa/senior-qa-engineer-2091100',2091100)}
out=[]
for name,(u,ident) in cards.items():
 t=time.time();req=urllib.request.Request(u,headers={'User-Agent':UA})
 try:
  with urllib.request.urlopen(req,timeout=30) as x:b=x.read();st=x.status;final=x.geturl()
 except Exception as e:
  try: urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'curl/8.5'}),timeout=30)
  except urllib.error.HTTPError as z: b=z.read();st=z.code;final=z.geturl()
  except Exception as z: b=b'';st='ERROR';final=str(z)
 (R/f'card_{name}.html').write_bytes(b)
 text=b.decode('utf-8','replace')
 # JSON-LD evidence
 ld=[]
 for s in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',text,re.S|re.I):
  try: ld.append(json.loads(s))
  except: pass
 out.append({'name':name,'url':u,'id':ident,'status':st,'final':final,'ms':round((time.time()-t)*1000),'bytes':len(b),'jsonld':ld,'text_excerpt':re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',text))[:1200]})
 time.sleep(.4)
(O/'direct_cards_evidence.json').write_text(json.dumps(out,indent=2,ensure_ascii=False))
print([(x['name'],x['status'],x['bytes']) for x in out])
