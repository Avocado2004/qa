import json,re,time,html,requests
from bs4 import BeautifulSoup as B
from pathlib import Path
from datetime import datetime,timezone
C='2026-09-24_cycle-10'; O=Path('/opt/data/results/vac-2026-09-24_cycle-10-source-linkedin.com'); W=O/'.worker-state'
for x in [O,W,O/'raw',O/'completed']: x.mkdir(parents=True,exist_ok=True)
now=lambda:datetime.now(timezone.utc).isoformat(); J=lambda p,o:p.write_text(json.dumps(o,ensure_ascii=False,indent=2))
Q=Path('/opt/data/results/cycles/2026-09-24_cycle-10/worker-pool/queue.json')
def beat(a):
 q=json.loads(Q.read_text()); j=next(x for x in q['jobs'] if x.get('owner')=='worker-1');j['heartbeat_at']=now();j['next_action']=a;J(Q,q)
queries=[(r,l,rem) for r in ['Softwaretester','QA Engineer Qualitätssicherung','Testautomatisierer','Gamedev QA'] for l,rem in [('Berlin',0),('Leipzig',0),('Dresden',0),('Germany',1)]]
M={'cycle_id':C,'source_id':'linkedin.com','owner':'worker-1','status':'running','started_at':now(),'governing_skill':'qa-vacancy-search-de'};K={'cycle_id':C,'source_id':'linkedin.com','status':'running','cursor':{},'updated_at':now(),'attempts':[]};F={'cycle_id':C,'source_id':'linkedin.com','failures':[]};P={'cycle_id':C,'source_id':'linkedin.com','sequential':True,'queries':queries,'location_axes':['Berlin','Leipzig','Dresden','Germany-wide Remote'],'role_axes':['Manual WEB QA','Software Test / Automation','Gamedev QA','Other QA Roles']}
for p,o in [(W/'manifest.json',M),(W/'checkpoint.json',K),(W/'failures.json',F),(W/'plan.json',P)]:J(p,o)
s=requests.Session();s.headers['User-Agent']='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36';s.headers['Accept-Language']='de-DE,de;q=.9';cards=[];seen=set()
for i,(r,l,rem) in enumerate(queries):
 for st in (0,25):
  K['cursor']={'query_index':i,'start':st,'card_index':0};K['updated_at']=now();J(W/'checkpoint.json',K);beat(f'query {i+1}/16 start {st}')
  u='https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search'; par={'keywords':r,'location':l,'f_TPR':'r2592000','start':str(st)}
  if rem:par['f_WT']='2'
  try:
   z=s.get(u,params=par,timeout=25);K['attempts'].append({'url':z.url,'status':z.status_code,'bytes':len(z.content)});(O/'raw'/f'list_{i}_{st}.html').write_bytes(z.content)
   if z.status_code in (403,429):F['failures'].append({'type':'http_block','status':z.status_code,'url':z.url,'at':now()});J(W/'failures.json',F);time.sleep(5)
   z.raise_for_status()
   for c in B(z.text,'html.parser').select('li'):
    a=c.select_one('a.base-card__full-link,a[href*="/jobs/view/"]')
    if not a:continue
    h=a.get('href','').split('?')[0];m=re.search(r'/jobs/view/(?:[^/]*?-)?([^/?]+)/?$',h)
    if not m or m.group(1) in seen:continue
    jid=m.group(1);seen.add(jid);t=c.select_one('.base-search-card__title,.sr-only,h3');co=c.select_one('.base-search-card__subtitle,.art-subtitle,h4');lo=c.select_one('.job-search-card__location,.base-search-card__metadata')
    cards.append({'id':jid,'url':f'https://www.linkedin.com/jobs/view/{jid}/','title':html.unescape(t.get_text(' ',strip=True) if t else 'Unknown'),'company':co.get_text(' ',strip=True) if co else 'Unknown','cardloc':lo.get_text(' ',strip=True) if lo else '','scope':l,'remote_query':bool(rem)})
  except Exception as e:F['failures'].append({'type':'request','error':repr(e),'at':now()});J(W/'failures.json',F)
  time.sleep(.6)
rows=[]
for n,c in enumerate(cards[:120]):
 K['cursor']={'query_index':16,'start':50,'card_index':n};J(W/'checkpoint.json',K);beat(f'card {n+1}/{min(len(cards),120)}')
 try:
  z=s.get(c['url'],timeout=25);K['attempts'].append({'url':z.url,'status':z.status_code,'bytes':len(z.content)});(O/'raw'/f"card_{n}.html").write_bytes(z.content)
  if z.status_code in (403,429):raise Exception('blocked '+str(z.status_code))
  x=' '.join((B(z.text,'html.parser').select_one('main') or B(z.text,'html.parser')).stripped_strings);t=x.lower();(O/'raw'/f'card_{n}.txt').write_text(x)
  if not re.search(r'qualitätssicherung|softwaretest|test engineer|testautomatis|qa engineer|qa analyst|game.?test|tester',t):continue
  eligible=any(a in t for a in re.split('[ ,]+',c['scope']));remote=bool(re.search(r'remote|homeoffice|home-office|mobiles arbeit',t))
  if not(eligible or(c['remote_query'] and remote and re.search(r'deutschland|germany',t))):continue
  role='Gamedev QA' if re.search(r'game|spiel',t) else ('Software Test / Automation' if re.search(r'automatis|test engineer|testingenieur|software test',t) else ('Manual WEB QA' if re.search(r'web|qa|manuell|manual',t) else 'Other QA Roles'))
  rows.append({**c,'location':'Germany-wide Remote' if c['scope']=='Germany' else c['scope'],'role':role,'mode':'Remote' if remote and not eligible else ('Hybrid' if 'hybrid' in t else 'Unknown')})
 except Exception as e:F['failures'].append({'type':'card','url':c['url'],'error':repr(e),'at':now()})
 time.sleep(.35)
lines=['# LinkedIn Jobs','',f'Accepted rows: {len(rows)}','','| # | Position | Company | Location axis | Role axis | Posted | Work mode |','|---:|---|---|---|---|---|---|']
for n,r in enumerate(rows,1):lines.append(f"| {n} | [{r['title'].replace('|','/')}]({r['url']}) | {r['company'].replace('|','/')} | {r['location']} | {r['role']} | {r['cardloc'] or 'Unknown'} | {r['mode']} |")
(O/'result.md').write_text('\n'.join(lines)+'\n');(O/'source_coverage.md').write_text(f'# Source coverage\n\n- Cycle: {C}\n- Source: linkedin.com only\n- Sequential guest API listing and direct-card analysis\n- Queries: 16 (4 roles × 4 location/work-mode axes)\n- Unique cards discovered: {len(cards)}\n- Cards opened: {min(len(cards),120)}\n- Accepted: {len(rows)}\n- Failures: {len(F["failures"])}\n- Evidence: raw/, provenance.json, .worker-state/\n')
J(O/'provenance.json',{'cycle_id':C,'source_id':'linkedin.com','queries':queries,'attempts':K['attempts'],'raw_candidates':len(cards),'cards_opened':min(len(cards),120),'accepted':len(rows),'methods':['guest API','direct-card HTTP'],'completed_at':now()});M.update(status='complete',completed_at=now(),raw_candidates=len(cards),accepted_rows=len(rows),failures=len(F['failures']));K.update(status='complete',updated_at=now(),cursor={'query_index':16,'start':50,'card_index':min(len(cards),120)},raw_candidates=len(cards),accepted_rows=len(rows))
for p,o in [(W/'manifest.json',M),(W/'checkpoint.json',K),(W/'failures.json',F)]:J(p,o)
print(json.dumps({'source':'linkedin.com','cards':len(cards),'accepted':len(rows),'failures':len(F['failures'])}))
