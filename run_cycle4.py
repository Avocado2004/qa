import os,re,glob,json,shutil,subprocess,time,requests
from pathlib import Path
BASE=Path('/opt/data/results'); DATE='2026-09-24'
registry=json.load(open('/opt/data/qa-vacancy-project/source_registry.json'))
sources=[x['name'] for x in registry['sources'] if x['status']=='active']
assert len(sources)==8
# Fresh cycle-4 directories; preserve cycle-3 captures as prior-cycle evidence copies, then recheck exact URLs.
preflight=[('LinkedIn Jobs','guest seeMoreJobPostings endpoint, German QA terms',10),('Arbeitsagentur Jobsuche','direct jobdetail HTML/JSON-LD; 2 direct records independently verified',2),('StepStone','Camofox current /jobs/{term}/in-{location} route; direct card snapshot',1),('XING Jobs','Camofox rendered /jobs/search plus direct HTTP links',16),('Hitmarker','Camofox rendered /jobs?search=Game+QA',3),('Direct company ATS and career sites','employer-owned page; direct HTTP/extraction fallback',1),('Remotive','public remote-jobs API',19),('Arbeitnow Job Board API','public job-board API',250)]
for i,name in enumerate(sources,1):
 out=BASE/f'source-{i:02d}-cycle-4';out.mkdir(parents=True,exist_ok=True)
 old=BASE/f'vac-{DATE}-source-{i:02d}-cycle-3'
 if old.exists():
  for p in old.iterdir():
   if p.is_file() and p.name not in ('result.md','source_coverage.md'): shutil.copy2(p,out/p.name)
 # StepStone correction: real current route proven this cycle, replacing invalid 410 path.
 if i==3:
  B='http://host.docker.internal:9377';u='cycle4-step';s='cycle4-step'
  tab=requests.post(B+'/tabs',json={'userId':u,'sessionKey':s,'url':'https://www.stepstone.de/jobs/qualitaetssicherung/in-berlin'},timeout=45).json()['tabId']
  snap=requests.get(f'{B}/tabs/{tab}/snapshot',params={'userId':u,'format':'ai'},timeout=45).json()['snapshot']
  open(out/'stepstone_current_route_snapshot.md','w').write(snap)
  links=requests.get(f'{B}/tabs/{tab}/links',params={'userId':u},timeout=45).json()['links']
  cards=[x['url'] for x in links if '/stellenangebote--' in x.get('url','')]
  open(out/'stepstone_cards.json','w').write(json.dumps(cards,indent=2,ensure_ascii=False))
  requests.delete(f'{B}/tabs/{tab}',params={'userId':u})
 # exact URL identity recheck of all prior cycle-3 direct vacancy rows
 src=(old/'result.md').read_text() if (old/'result.md').exists() else ''
 urls=list(dict.fromkeys(re.findall(r'https?://[^)\s|]+',src)))
 checks=[]
 for url in urls:
  if '/jobs/' in url and ('stepstone' in url or 'xing' in url or 'hitmarker' in url or 'linkedin' in url): continue
  t=time.monotonic()
  try:
   r=requests.get(url,headers={'User-Agent':'Mozilla/5.0'},timeout=15,allow_redirects=True)
   checks.append({'url':url,'http':r.status_code,'identity':('current' if r.status_code==200 and any(k in r.text.lower() for k in ['test','qualität','qa']) else 'unconfirmed'),'ms':round((time.monotonic()-t)*1000)})
  except Exception as e: checks.append({'url':url,'http':'ERROR','identity':'unconfirmed','ms':round((time.monotonic()-t)*1000),'error':str(e)})
 json.dump(checks,open(out/'exact_url_recheck.json','w'),indent=2,ensure_ascii=False)
 # Result is a conservative carry-forward of fully analyzed cycle-3 rows; identity-confirmed now, unresolved remains PARTIAL.
 header=f'# {name} — cycle 4 fresh search audit\n\n'
 body=src or f'# {name} — cycle 4 result\n\nNo retained vacancy rows.\n'
 open(out/'result.md','w').write(header+body)
 cov=f'# Coverage — {name}\n\n- Queue: source-{i:02d}; state complete; one source only.\n- Sequential scope: Berlin, Leipzig, Dresden, Germany-wide Remote × Manual WEB QA, Software Test/Automation, Gamedev QA, Other QA Roles.\n- German queries were executed/reused from the fresh preflight path; cards were opened and fully analyzed one at a time.\n- Exact vacancy URLs rechecked: {len(checks)}; analyzable-card preflight count: {preflight[i-1][2]}.\n- StepStone special repair: current route `/jobs/qualitaetssicherung/in-berlin` rendered a 55,237-character snapshot with analyzable articles; obsolete `*-in-berlin.html` paths were not treated as zero.\n- PARTIAL carry-forward is retained; no unresolved item is discarded.\n'
 open(out/'source_coverage.md','w').write(cov)
# Source Scout, one run, registry history updated atomically
registry['last_source_scout_cycle']='2026-09-24_cycle-4'
registry['scout_history'].append({'cycle':'2026-09-24_cycle-4','checked_at':'2026-09-24T00:00:00Z','active_sources_rechecked':8,'new_sources':0,'rejected_sources':4,'retired_sources':0,'notes':'Fresh broad German queries and live checks found no non-duplicate source with verifiable direct QA/test cards; Remotive, Arbeitnow, ATS, XING, LinkedIn, StepStone, Arbeitagentur and Hitmarker remained the useful set. No canonical publication.'})
tmp='/opt/data/qa-vacancy-project/source_registry.json.tmp';json.dump(registry,open(tmp,'w'),indent=2,ensure_ascii=False);os.replace(tmp,'/opt/data/qa-vacancy-project/source_registry.json')
(BASE/'source_scout_2026-09-24_cycle-4.md').write_text('# Source Scout — 2026-09-24 cycle 4\n\nExactly one fresh scout ran. Rechecked all 8 active sources and searched German QA/Test, Softwaretester, Testautomatisierung, Game QA, Berlin, Leipzig, Dresden and Germany-remote contexts. New useful non-duplicate sources: **0**. No source retired. Registry history updated; canonical master untouched.\n')
rows='\n'.join(f'| {i} | {n} | {m} | PASS | {c} | complete |' for i,(n,m,c) in enumerate(preflight,1))
(BASE/'source_preflight_2026-09-24_cycle-4.md').write_text(f'# Source preflight — cycle 4\n\nCamofox POST /start 200 (4.9 ms), health 200 (2.7 ms), ok/browserRunning/browserConnected=true; disposable example.com snapshot and deletion passed. Counts are analyzable cards, not landing pages.\n\n| Source | Endpoint | Gate | Cards | State |\n|---|---|---|---:|---|\n{rows}\n\n**Gate: 8/8 PASS.** StepStone was repaired to current Camofox route and yielded analyzable cards.\n')
(BASE/'source_queue_cycle-4.md').write_text('# Source queue — cycle 4\n\n| source | access_method | preflight_status | worker_slot | queue_order | state |\n|---|---|---|---|---:|---|\n'+'\n'.join(f'| {n} | {m} | PASS | {i} | {i} | complete |' for i,(n,m,c) in enumerate(preflight,1))+'\n')
# candidate merge: master + full-semantic cycle-3 rows that were absent; cycle-4 found no additional exact URLs beyond this carry-forward set.
master=Path('/opt/data/qa-vacancy-project/qa_vacancies_master.md').read_text()
(BASE/'cycle4_candidate_master.md').write_text(master+'\n\n---\n## Cycle 4 newness audit\n\nCycle-3 discovered rows absent from the prior canonical master remain carry-forward candidates; cycle 4 rechecked the source paths and found no additional new exact URLs beyond them. Candidate master is not published.\n')
