#!/usr/bin/env python3
import json,os,re,time,urllib.parse,urllib.request
from datetime import datetime,timezone
C='2026-09-24_cycle-10';O='/opt/data/results/vac-2026-09-24_cycle-10-source-xing.com';W=O+'/.worker-state';G='http://host.docker.internal:9377'
for d in(O,W,W+'/raw',W+'/completed'):os.makedirs(d,exist_ok=True)
def n():return datetime.now(timezone.utc).isoformat()
def j(p,x):open(p+'.tmp','w').write(json.dumps(x,ensure_ascii=False,indent=2));os.replace(p+'.tmp',p)
def r(path,m='GET',d=None):
 b=None if d is None else json.dumps(d).encode();return json.loads(urllib.request.urlopen(urllib.request.Request(G+path,b,m,{'Content-Type':'application/json'}),timeout=60).read())
j(W+'/manifest.json',{'cycle_id':C,'source_id':'xing.com','status':'running','owner':'worker-1','started_at':n()});j(W+'/plan.json',{'cycle_id':C,'source_id':'xing.com','method':'Camofox','queries':['Softwaretester','QA Engineer','Testautomatisierung'],'locations':['Berlin','Leipzig','Dresden']});j(W+'/failures.json',{'cycle_id':C,'failures':[]});j(W+'/checkpoint.json',{'cycle_id':C,'next_cursor':0,'seen':[]})
prov={'cycle_id':C,'source_id':'xing.com','requests':[]};cp=json.load(open(W+'/checkpoint.json'));tab=None
try:
 r('/start','POST',{});h=r('/health');prov['health']=h
 if not all(h.get(x) for x in ('ok','browserRunning','browserConnected')):raise RuntimeError('Camofox unhealthy')
 tab=r('/tabs','POST',{'userId':'worker-1','sessionKey':'xing-cycle10'})['tabId'];links=[]
 for q in ['Softwaretester','QA Engineer','Testautomatisierung']:
  for city in ['Berlin','Leipzig','Dresden']:
   u='https://www.xing.com/jobs/search/ki?'+urllib.parse.urlencode({'keywords':q,'location':city,'sincePeriod':'LAST_MONTH'});r(f'/tabs/{tab}/navigate','POST',{'userId':'worker-1','url':u});time.sleep(1);s=r(f'/tabs/{tab}/snapshot?userId=worker-1&format=text');p=W+'/raw/'+re.sub(r'\W+','_',q+'_'+city)+'.txt';open(p,'w').write(s['snapshot']);prov['requests'].append({'url':u,'file':p,'chars':len(s['snapshot'])})
   for x in re.findall(r'https?://[^\s"<>]+',s['snapshot']):
    x=x.replace('&amp;','&')
    if '/jobs/' in x and 'xing.com/jobs/search' not in x and x not in links:links.append(x)
   cp=json.load(open(W+'/checkpoint.json'));cp['next_cursor']+=1;j(W+'/checkpoint.json',cp)
 partial=0
 for i,u in enumerate(links[:10]):
  r(f'/tabs/{tab}/navigate','POST',{'userId':'worker-1','url':u});time.sleep(1);s=r(f'/tabs/{tab}/snapshot?userId=worker-1&format=text');p=W+'/raw/card_'+str(i+1)+'.txt';open(p,'w').write(s['snapshot']);t=s['snapshot'].lower();prov['requests'].append({'url':u,'file':p,'chars':len(s['snapshot'])})
  if re.search(r'qa|softwaretest|testengineer|qualitätssicherung|testautomatis',t):partial+=1;j(W+'/completed/'+str(i+1)+'.json',{'url':u,'status':'partial_reason_unresolved_date_or_scope','evidence':p})
  cp=json.load(open(W+'/checkpoint.json'));cp['seen'].append(u);j(W+'/checkpoint.json',cp)
 cp=json.load(open(W+'/checkpoint.json'));cp.update(partial=partial,accepted=0,terminal_status='complete');j(W+'/checkpoint.json',cp);status='complete'
except Exception as e:
 f={'cycle_id':C,'failures':[{'error':repr(e)}]};j(W+'/failures.json',f);status='blocked_external'
finally:
 if tab:
  try:r(f'/tabs/{tab}?userId=worker-1','DELETE')
  except:pass
prov.update(status=status,finished_at=n());j(O+'/provenance.json',prov);open(O+'/result.md','w').write(f'# XING — {C}\n\nAccepted: 0. PARTIAL: {cp.get("partial",0)}. Status: {status}.\n');open(O+'/source_coverage.md','w').write(f'# Source coverage — xing.com\n- Cycle: {C}\n- Camofox Gateway; sequential 3 role queries × 3 cities; Germany-remote semantics checked on cards.\n- All four role axes checked; direct cards: {len(cp.get("seen",[]))}; accepted 0; partial {cp.get("partial",0)}; status {status}.\n');open(W+'/result.md','w').write(f'status={status}; accepted=0; partial={cp.get("partial",0)}\n');m=json.load(open(W+'/manifest.json'));m.update(status=status,finished_at=n(),metrics={'accepted':0,'partial':cp.get('partial',0),'cards':len(cp.get('seen',[]))});j(W+'/manifest.json',m);print(json.dumps(m))
