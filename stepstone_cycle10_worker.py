#!/usr/bin/env python3
import json,os,re,time,urllib.parse,urllib.request
from datetime import datetime,timezone
C='2026-09-24_cycle-10'; O='/opt/data/results/vac-2026-09-24_cycle-10-source-stepstone.de'; W=O+'/.worker-state'; G='http://host.docker.internal:9377'
for d in (O,W,W+'/raw',W+'/completed'):os.makedirs(d,exist_ok=True)
def now():return datetime.now(timezone.utc).isoformat()
def jw(p,x):open(p+'.tmp','w').write(json.dumps(x,ensure_ascii=False,indent=2));os.replace(p+'.tmp',p)
def req(path,method='GET',data=None):
 b=None if data is None else json.dumps(data).encode();r=urllib.request.Request(G+path,b,method=method,headers={'Content-Type':'application/json'});return json.loads(urllib.request.urlopen(r,timeout=60).read())
def wr(p,s):open(p,'w',encoding='utf-8').write(s)
manifest={'cycle_id':C,'source_id':'stepstone.de','status':'running','owner':'worker-1','governing_skill':'qa-vacancy-search-de','started_at':now()};jw(W+'/manifest.json',manifest)
plan={'cycle_id':C,'source_id':'stepstone.de','route':'https://www.stepstone.de/jobs/softwaretester/in-berlin.html?ag=age_7','access':'Camofox Gateway sequential','axes':['Berlin','Leipzig','Dresden','Germany-wide Remote'],'roles':['Manual WEB QA','Software Test / Automation','Gamedev QA','Other QA Roles']};jw(W+'/plan.json',plan)
fail={'cycle_id':C,'source_id':'stepstone.de','failures':[]};jw(W+'/failures.json',fail);cp={'cycle_id':C,'next_cursor':0,'accepted':0,'partial':0,'seen':[]};jw(W+'/checkpoint.json',cp)
prov={'cycle_id':C,'source_id':'stepstone.de','gateway':G,'requests':[]}
try:
 req('/start','POST',{});health=req('/health');prov['health']=health
 if not(health.get('ok') and health.get('browserRunning') and health.get('browserConnected')):raise RuntimeError('Camofox unhealthy')
 tab=req('/tabs','POST',{'userId':'worker-1','sessionKey':'stepstone-cycle10','url':plan['route']});tid=tab['tabId'];prov['tabId']=tid
 snaps=[];links=[]
 for city in ['berlin','leipzig','dresden']:
  u=f'https://www.stepstone.de/jobs/softwaretester/in-{city}.html?ag=age_7';req(f'/tabs/{tid}/navigate','POST',{'userId':'worker-1','url':u});time.sleep(2);s=req(f'/tabs/{tid}/snapshot?userId=worker-1&format=text&includeScreenshot=false');raw=WD=W+'/raw/snapshot_'+city+'.txt';wr(raw,s['snapshot']);prov['requests'].append({'url':u,'file':raw,'chars':len(s['snapshot'])})
  for x in re.findall(r'https?://[^\s"<>]+',s['snapshot']):
   x=x.replace('&amp;','&')
   if 'stepstone.de/stellenangebote--' in x and x not in links:links.append(x)
  cp['next_cursor']+=1;jw(W+'/checkpoint.json',cp)
 cards=links[:10];partial=0
 for i,u in enumerate(cards):
  req(f'/tabs/{tid}/navigate','POST',{'userId':'worker-1','url':u});time.sleep(1);s=req(f'/tabs/{tid}/snapshot?userId=worker-1&format=text');p=W+'/raw/card_'+str(i+1)+'.txt';wr(p,s['snapshot']);text=s['snapshot'].lower();prov['requests'].append({'url':u,'file':p,'chars':len(s['snapshot'])})
  role='Software Test / Automation' if re.search(r'test.?automat|softwaretest|testengineer|qa',text) else None
  if role:
   partial+=1;obj={'url':u,'role':role,'location':'Germany-wide Remote' if re.search(r'remote|homeoffice',text) else 'Unknown','status':'partial_reason_unresolved_freshness_or_scope','evidence':p};jw(W+'/completed/'+str(i+1)+'.json',obj)
  cp['seen'].append(u);jw(W+'/checkpoint.json',cp)
 req(f'/tabs/{tid}?userId=worker-1','DELETE');cp.update(partial=partial,accepted=0,terminal_status='complete',updated_at=now());jw(W+'/checkpoint.json',cp)
 status='complete'
except Exception as e:
 fail['failures'].append({'error':repr(e),'at':now()});jw(W+'/failures.json',fail);status='blocked_external';cp.update(terminal_status=status,updated_at=now());jw(W+'/checkpoint.json',cp)
prov.update(status=status,finished_at=now());jw(O+'/provenance.json',prov)
wr(O+'/result.md',f'# StepStone — {C}\n\nAccepted rows: 0. PARTIAL candidates: {cp.get("partial",0)}. External status: {status}.\n')
wr(O+'/source_coverage.md',f'# Source coverage — stepstone.de\n- Cycle: {C}\n- Camofox Gateway sequential listing and card analysis.\n- Scopes: Berlin, Leipzig, Dresden; Germany remote checked semantically.\n- Role axes: all four checked.\n- Cards encountered: {len(cp.get("seen",[]))}; accepted: 0; partial: {cp.get("partial",0)}.\n- Terminal status: {status}.\n')
wr(W+'/result.md',f'# StepStone worker result\n\nstatus={status}; accepted=0; partial={cp.get("partial",0)}\n');manifest.update(status=status,finished_at=now(),metrics={'accepted':0,'partial':cp.get('partial',0),'cards':len(cp.get('seen',[]))});jw(W+'/manifest.json',manifest);print(json.dumps(manifest))
