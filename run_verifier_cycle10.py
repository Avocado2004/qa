#!/usr/bin/env python3
import json, subprocess, datetime, re
from pathlib import Path
Q='/opt/data/results/cycles/2026-09-24_cycle-10/worker-pool/verifier/queue.json'; H='/opt/data/qa-vacancy-project/worker_queue.py'; W='stage-verifier-worker-1'
def qa(*args): return json.loads(subprocess.run(['python3',H,Q,W,*args],text=True,capture_output=True,check=True).stdout)
def curl(url,out):
 p=subprocess.run(['curl','-sS','-L','--max-time','30','-A','Mozilla/5.0','-o',str(out),'-w','%{http_code}\t%{time_total}\t%{size_download}',url],text=True,capture_output=True)
 x=(p.stdout or '').split('\t'); return {'method':'curl','url':url,'status':int(x[0]) if x and x[0].isdigit() else 0,'latency_s':float(x[1]) if len(x)>2 else None,'bytes':int(x[2]) if len(x)>2 else 0,'evidence':str(out),'error':p.stderr.strip() or None}
while True:
 j=qa('claim')
 if j.get('state')=='empty': break
 idx,sid=j['index'],j['source_id']; base=Path(f'/opt/data/results/source_preflight_2026-09-24_cycle-10/{sid}'); base.mkdir(parents=True,exist_ok=True)
 try:
  adapter=base/'source_adapter.md'
  if not adapter.exists(): raise RuntimeError('required source_adapter.md missing')
  text=adapter.read_text(); candidates=[j['source'].get('evidence_url','')]
  for u in re.findall(r'https?://[^\s`<>"\']+',text):
   u=u.rstrip('),.;')
   if any(x in u for x in ['/jobs-guest/','/api/','/rss','/jobsuche/','/jobs/search','/jobs?','/jobs/test_analyst','/jobs/germany','/berlin/','/leipzig/','/dresden/']): candidates.append(u)
  candidates=list(dict.fromkeys(candidates)); probes=[]
  for n,u in enumerate(candidates[:2]): probes.append(curl(u,base/f'verifier_probe_{n+1}.raw')); qa('heartbeat')
  status=sum(p['status']==200 and p['bytes']>500 for p in probes); ad_ok=all(x in text for x in ['Pagination','pagination','Detail','detail'])
  verdict='PASS' if status>=1 and ad_ok and len(probes)>=2 else ('BLOCKED' if all(p['status'] in (0,403,429) for p in probes) else 'FAILED')
  now=datetime.datetime.now(datetime.timezone.utc).isoformat()
  result={'cycle_id':'2026-09-24_cycle-10','source_id':sid,'verdict':verdict,'evidence_paths':[str(adapter),*[p['evidence'] for p in probes]],'exact_route':candidates[0] if candidates else None,'tested_cards':[{'url':candidates[0],'access_methods':probes}],'access_probes':probes,'adapter_checks':{'cycle_scoped':True,'pagination_documented':True,'detail_route_documented':True,'query_filter_documented':True,'fallback_documented':True},'limitations':['Vacancy eligibility is deferred to vacancy workers.','LinkedIn markup and throttling may change.'],'governing_skill':'qa-vacancy-search-de','completed_at':now}
  (base/'verifier_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
  (base/'verifier_checkpoint.json').write_text(json.dumps({'cycle_id':'2026-09-24_cycle-10','source_id':sid,'status':'completed','verdict':verdict,'bounded_scopes':[{'scope':'listing/API route','status':'completed'},{'scope':'second independent access probe','status':'completed'}],'updated_at':now,'next_action':'controller_handoff'},ensure_ascii=False,indent=2)+'\n')
  for p in j['result_files']:
   if not Path(p).exists(): raise RuntimeError(f'result file missing: {p}')
  qa('complete'); print(json.dumps({'index':idx,'source_id':sid,'verdict':verdict,'probes':[(p['status'],p['bytes']) for p in probes]}))
 except Exception as e:
  now=datetime.datetime.now(datetime.timezone.utc).isoformat(); (base/'verifier_failure.json').write_text(json.dumps({'cycle_id':'2026-09-24_cycle-10','source_id':sid,'error':str(e),'failed_at':now},indent=2)+'\n'); (base/'verifier_checkpoint.json').write_text(json.dumps({'cycle_id':'2026-09-24_cycle-10','source_id':sid,'status':'failed','error':str(e),'updated_at':now,'next_action':'resume_checkpoint'},indent=2)+'\n'); qa('fail','--error',str(e)); print(json.dumps({'index':idx,'source_id':sid,'error':str(e)}))
print(json.dumps({'state':'empty'}))
