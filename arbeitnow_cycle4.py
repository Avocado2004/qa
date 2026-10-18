import json, re, time, html, os
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from datetime import date, datetime
BASE='/opt/data/results/vac-2026-09-24-source-08-cycle-4'
RAW=BASE+'/raw'; EV=BASE+'/source_coverage/evidence'
os.makedirs(RAW,exist_ok=True); os.makedirs(EV,exist_ok=True)
UA='Mozilla/5.0 (compatible; QA-vacancy-audit/1.0)'
def get(u, binary=False):
 r=Request(u,headers={'User-Agent':UA,'Accept':'application/json' if 'api/job-board' in u else 'text/html,application/xhtml+xml'})
 last=None
 for attempt in range(7):
  try:
   with urlopen(r,timeout=45) as x: return x.status,x.geturl(),x.read()
  except Exception as e:
   last=e
   if getattr(e,'code',None)==429: time.sleep(15*(attempt+1)); continue
   raise
 raise last
allrows=[]; pages=[]; page=1
resume=RAW+'/arbeitnow_page_18.json'
if os.path.exists(resume):
 allrows=[]
 for p in range(1,18):
  d=json.load(open(f'{RAW}/arbeitnow_page_{p:02}.json')); rows=d.get('data',[]); allrows.extend(rows)
  pages.append({'page':p,'http':200,'records':len(rows),'bytes':os.path.getsize(f'{RAW}/arbeitnow_page_{p:02}.json'),'next':(d.get('links') or {}).get('next')})
 page=19
while page<=100:
 u='https://www.arbeitnow.com/api/job-board-api'+('' if page==1 else f'?page={page}')
 status,final,b=get(u); open(f'{RAW}/arbeitnow_page_{page:02}.json','wb').write(b)
 d=json.loads(b); rows=d.get('data',[]); pages.append({'page':page,'http':status,'final_url':final,'records':len(rows),'bytes':len(b),'next':(d.get('links') or {}).get('next')})
 allrows.extend(rows); print(page,len(rows),flush=True)
 if not rows or not (d.get('links') or {}).get('next'): break
 page+=1; time.sleep(1.1)
json.dump(allrows,open(BASE+'/arbeitnow_all_records.json','w'),ensure_ascii=False,indent=2)
json.dump(pages,open(EV+'/pagination.json','w'),ensure_ascii=False,indent=2)
# broad all-axis local discovery
role=re.compile(r'\b(qa|quality assurance|quality engineer|software test(?:er|ing)?|test engineer|test automation|testautomatis|testmanager|test lead|game test(?:er|ing)?|game qa|spieletester|softwaretester|hardware test|flight test|propulsion test|testingenieur|qualitätssicherung|qualitattssicherung)\b',re.I)
loc=re.compile(r'berlin|leipzig|dresden|germany|deutschland|remote|homeoffice|home office',re.I)
out=[]
for r in allrows:
 text=' '.join(str(r.get(k,'')) for k in ('title','description','company_name'))
 if role.search(text) and loc.search(text): out.append(r)
json.dump(out,open(BASE+'/candidates.json','w'),ensure_ascii=False,indent=2)
# deterministic ranked shortlist, including carryforward by URL/title
carry=['indiekidz-gmbh/software-test-qa','bruggen-engineering-gmbh/lead-engineer-automotive','1komma50/senior-qa','stark/flying-b-2-flight-test']
rank=[]
for r in out:
 text=html.unescape(re.sub('<[^>]+>',' ',str(r.get('title',''))+' '+r.get('description','')))
 score=sum(x for p,x in [(role.search(text),4),((r.get('remote') is True),1), (re.search(r'berlin|leipzig|dresden',text,re.I),3), (re.search(r'qa|software test|game test|flight test|propulsion test|test automation',text,re.I),5)] if p)
 carrybonus=any(c in r.get('url','') for c in carry)
 if score>=7 or carrybonus: rank.append((score+10*carrybonus,r.get('created_at',''),r))
rank.sort(key=lambda x:(-x[0],x[1]),reverse=True)
sel=[]
for _,_,r in rank:
 u=r.get('url','')
 if u and u not in [x.get('url') for x in sel]: sel.append(r)
sel=sel[:40]
results=[]
for i,r in enumerate(sel,1):
 u=r.get('url'); ev={'api':r}
 try:
  st,final,b=get(u); slug=re.sub(r'[^a-z0-9]+','_',urlparse(u).path.lower())[:100]
  fn=f'{EV}/direct_{i:02}_{slug}.html'; open(fn,'wb').write(b)
  s=b.decode('utf-8','replace')
  dates=re.findall(r'"datePosted"\s*:\s*"([^"]+)',s)
  ev.update({'http':st,'final_url':final,'bytes':len(b),'evidence_file':os.path.basename(fn),'datePosted':dates[:3],'title_in_page':r.get('title') in html.unescape(s)})
 except Exception as e: ev.update({'error':repr(e)})
 results.append(ev); time.sleep(.35)
json.dump(results,open(EV+'/direct_cards.json','w'),ensure_ascii=False,indent=2)
print('total',len(allrows),'pages',len(pages),'broad',len(out),'shortlist',len(sel))
