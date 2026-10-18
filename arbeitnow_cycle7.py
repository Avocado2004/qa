import json,re,time,html,os
from urllib.request import Request,urlopen
from urllib.parse import urlparse
from datetime import datetime,timezone
BASE='/opt/data/results/vac-2026-09-24-arbeitnow-cycle-7'; RAW=BASE+'/raw'; os.makedirs(RAW,exist_ok=True)
UA='Mozilla/5.0 (compatible; QA-vacancy-audit/1.0)'
def get(u,accept='application/json'):
 for a in range(7):
  try:
   with urlopen(Request(u,headers={'User-Agent':UA,'Accept':accept}),timeout=45) as r:return r.status,r.geturl(),r.read()
  except Exception as e:
   if getattr(e,'code',None)==429: time.sleep(15*(a+1)); continue
   raise
 raise RuntimeError('retry exhausted')
pages=[]; records=[]; page=1; seen=set()
while page<=300:
 u='https://www.arbeitnow.com/api/job-board-api'+('' if page==1 else f'?page={page}')
 st,final,b=get(u); fn=f'{RAW}/arbeitnow_page_{page:03}.json'; open(fn,'wb').write(b)
 d=json.loads(b); rows=d.get('data',[]); nxt=(d.get('links') or {}).get('next')
 for r in rows:
  key=r.get('url') or r.get('slug') or json.dumps(r,sort_keys=True)
  if key not in seen: seen.add(key); records.append(r)
 pages.append({'page':page,'url':u,'http':st,'final_url':final,'records':len(rows),'unique_total':len(records),'bytes':len(b),'next':nxt})
 print(page,len(rows),len(records),flush=True)
 if not rows or not nxt: break
 page+=1; time.sleep(1.1)
json.dump(records,open(RAW+'/all_records_dedup.json','w'),ensure_ascii=False,indent=2); json.dump(pages,open(RAW+'/pagination.json','w'),ensure_ascii=False,indent=2)
# Discovery only; final acceptance below uses full detail/API text.
role=re.compile(r'\b(qa|quality assurance|quality engineer|software test(?:er|ing)?|test engineer|test automation|testautomatis|testmanager|test lead|game test(?:er|ing)?|game qa|spieletester|softwaretester|testingenieur|qualitätssicherung|qualitattssicherung|hardware test|flight test|propulsion test)\b',re.I)
target=re.compile(r'berlin|leipzig|dresden',re.I); de=re.compile(r'germany|deutschland|Deutschland',re.I)
cand=[]
for r in records:
 text=html.unescape(re.sub('<[^>]+>',' ',str(r.get('title',''))+' '+r.get('description','')))
 if role.search(text) and (target.search(text) or de.search(text) or r.get('remote') is True): cand.append(r)
# sequential full-card/API analysis
analyses=[]; accepted=[]
for i,r in enumerate(cand,1):
 u=r.get('url',''); ev={'source_record':r,'analysis_method':'full Arbeitnow API record, then direct card when available'}
 try:
  if u:
   st,final,b=get(u,'text/html,application/xhtml+xml'); slug=re.sub('[^a-z0-9]+','_',urlparse(u).path.lower())[:100]; fn=f'{RAW}/card_{i:03}_{slug}.html'; open(fn,'wb').write(b)
   s=html.unescape(re.sub('<[^>]+>',' ',b.decode('utf-8','replace'))); ev.update(http=st,final_url=final,bytes=len(b),evidence_file=os.path.basename(fn),title_confirmed=r.get('title','').lower() in s.lower())
  else: ev['http']=None; ev['error']='no direct URL'
 except Exception as e: ev.update(error=repr(e)); s=''
 # Semantic gate uses the source-owned API record only. Direct HTML may contain
 # navigation/related-job links and must not leak unrelated city/skill tokens.
 text=html.unescape(re.sub('<[^>]+>',' ',str(r.get('title',''))+' '+r.get('description','')))
 rc=role.search(text); city=next((c for c in ('Berlin','Leipzig','Dresden') if re.search(c,text,re.I)),None)
 remote=bool((r.get('remote') is True and de.search(text)) or re.search(r'(remote.{0,80}(germany|deutschland)|(germany|deutschland).{0,80}remote)',text,re.I))
 if not (rc and (city or remote)): verdict='REJECT'
 else:
  if re.search(r'game|spiel',text,re.I): cat='Gamedev QA'
  elif re.search(r'automat|test engineer|testingenieur',text,re.I): cat='Software Test / Automation'
  elif re.search(r'hardware|flight|propulsion',text,re.I): cat='Other QA Roles'
  else: cat='Manual WEB QA'
  if re.search(r'hybrid',text,re.I): mode='Hybrid'
  elif remote: mode='Remote'
  elif city: mode='Onsite'
  else: mode='Unknown'
  verdict='PASS'; accepted.append({'title':r.get('title'),'company':r.get('company_name'),'url':u,'location':city or 'Germany-wide Remote','role':cat,'posted':r.get('created_at'),'work_mode':mode,'record':r})
 ev.update(role_evidence=rc.group(0) if rc else None,target_city=city,germany_remote=remote,verdict=verdict); analyses.append(ev); time.sleep(.25)
# dedupe
uniq=[]; seen2=set()
for a in accepted:
 if a['url'] and a['url'] not in seen2: seen2.add(a['url']); uniq.append(a)
json.dump(analyses,open(RAW+'/sequential_analysis.json','w'),ensure_ascii=False,indent=2); json.dump(uniq,open(BASE+'/accepted.json','w'),ensure_ascii=False,indent=2)
# Russian result
lines=['# Arbeitnow — результаты cycle-7','',f'- Уникальных записей API: **{len(records)}**; страниц: **{len(pages)}**.','- Поиск охватил target scopes: Berlin, Leipzig, Dresden, Germany-wide Remote.','- Роли: Manual WEB QA, Software Test / Automation, Gamedev QA, Other QA Roles.','- Каждая найденная запись анализировалась последовательно по полному тексту; прямые карточки сохранены в `raw/`.','', '| # | Position | Company | Location axis | Role axis | Posted | Work mode |','|---:|---|---|---|---|---|---|']
for i,a in enumerate(uniq,1):
 esc=lambda x:str(x or '').replace('|','\\|')
 lines.append(f"| {i} | [{esc(a['title'])}]({a['url']}) | {esc(a['company'])} | {a['location']} | {a['role']} | {esc(a['posted'])} | {a['work_mode']} |")
open(BASE+'/result.md','w').write('\n'.join(lines)+'\n')
# coverage + provenance
json.dump({'source':'https://www.arbeitnow.com','api':'https://www.arbeitnow.com/api/job-board-api','checked_at':datetime.now(timezone.utc).isoformat(),'run':'2026-09-24_cycle-7','http_results':'see raw/pagination.json','records':len(records),'pages':len(pages),'candidates_fully_analyzed':len(cand),'accepted_unique':len(uniq),'access_methods':['public API listing with links.next pagination','direct job-card HTTP fetch after API record']},open(BASE+'/provenance.json','w'),ensure_ascii=False,indent=2)
open(BASE+'/coverage.md','w').write(f'''# Coverage / покрытие\n\n- Страниц API: {len(pages)}; уникальных сырых записей: {len(records)}.\n- Кандидатов, отобранных для полного последовательного анализа: {len(cand)}.\n- Проанализировано последовательно: {len(cand)}/{len(cand)}; пропусков внутри очереди нет.\n- Berlin: рассмотрено в полном объёме API; Leipzig: рассмотрено; Dresden: рассмотрено; Germany-wide Remote: рассмотрено.\n- Все четыре категории ролей рассмотрены; ни одна запись не классифицирована только по title/URL.\n- Результат: {len(uniq)} уникальных PASS.\n''')
print('DONE',len(records),len(pages),len(cand),len(uniq))
