import json, os, tempfile
root='/opt/data/qa-vacancy-project'
art='/opt/data/results/cycles/2026-09-24_cycle-9/artifacts'
os.makedirs(art,exist_ok=True)
now='2026-09-24T00:00:00Z'; cycle='2026-09-24_cycle-9'
rejected=[
 {'domain':'jobgether.com','reason':'Candidate API route returned HTTP 404; no accessible listing/direct-card evidence obtained.','evidence':[{'method':'requests GET','url':'https://jobgether.com/api/feed/job?keyword=qa','result':'HTTP 404'}]},
 {'domain':'jobicy.com','reason':'QA tag API route returned HTTP 400; no alternate current German direct-card evidence obtained.','evidence':[{'method':'requests GET','url':'https://jobicy.com/api/v2/remote-jobs?count=100&tag=qa','result':'HTTP 400'}]},
 {'domain':'devjobs.de','reason':'Direct HTTP returned HTTP 403; web extraction timed out. Two methods failed, so no verifiable current direct card/list.','evidence':[{'method':'curl -L','url':'https://devjobs.de/','result':'HTTP 403'},{'method':'web_extract','url':'https://devjobs.de/','result':'backend read timeout'}]},
 {'domain':'weworkremotely.com','reason':'Direct HTTP returned HTTP 403; web extraction timed out. Two methods failed, so no verifiable current direct card/list.','evidence':[{'method':'curl -L','url':'https://weworkremotely.com/remote-jobs/search?term=QA','result':'HTTP 403'},{'method':'web_extract','url':'https://weworkremotely.com/remote-jobs/search?term=QA','result':'backend read timeout'}]},
 {'domain':'honeypot.org','reason':'TLS certificate verification failed; web extraction timed out; no two-method live card evidence.','evidence':[{'method':'curl -L','url':'https://www.honeypot.org/?q=qa','result':'TLS certificate verification failure'},{'method':'web_extract','url':'https://www.honeypot.org/?q=qa','result':'backend read timeout'}]}
]
registry_path=root+'/source_registry.json'
with open(registry_path,encoding='utf-8') as f: reg=json.load(f)
entry={'cycle':cycle,'checked_at':now,'active_sources_rechecked':len(reg.get('sources',[])),'new_sources':0,'rejected_sources':len(rejected),'retired_sources':0,'notes':'Exactly one mandatory Source Scout completed for cycle 9. Camofox unavailable (CAMOFOX_URL unset). Exa MCP HTTP 429; SearXNG URL unset; crawl4ai-skill unavailable; keyless web extraction timed out. Built-in web search found no relevant candidates. Direct checks found no new source meeting two-method live evidence. Registry retained; public vacancy list untouched.'}
if not any(x.get('cycle')==cycle for x in reg.get('scout_history',[])): reg.setdefault('scout_history',[]).append(entry)
reg['last_source_scout_cycle']=cycle
fd,tmp=tempfile.mkstemp(dir=root,prefix='.source_registry.',suffix='.tmp',text=True)
with os.fdopen(fd,'w',encoding='utf-8') as f:
 json.dump(reg,f,ensure_ascii=False,indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
os.replace(tmp,registry_path)
out={'cycle_id':cycle,'governing_skill':'qa-vacancy-search-de','stage':'SOURCE_SCOUT','verdict':'PASS_NO_NEW_SOURCES','checked_at':now,'registry_path':registry_path,'additions':[],'rejected':rejected,'duplicates':[],'retired':[],'backend_evidence':[
 {'backend':'Camofox','status':'unavailable','failure':'CAMOFOX_URL unset in actual worker environment; controller owns repair/preflight.'},
 {'backend':'SearXNG JSON API','status':'unavailable','failure':'SEARXNG_URL unset.'},
 {'backend':'Exa MCP','status':'failed','failure':'HTTP 429 free MCP rate limit.'},
 {'backend':'crawl4ai-skill','status':'unavailable','failure':'command not found.'},
 {'backend':'web search','status':'completed','failure':'Four German discovery queries returned no relevant new candidates.'},
 {'backend':'direct HTTP/API','status':'completed','failure':'Jobgether 404; Jobicy 400; RemoteOK and Arbeitnow reachable but already registered; other candidate hosts lacked two successful methods.'}
], 'evidence':{'registry_source_count':len(reg.get('sources',[])),'confirmed_addition_count':0,'registry_updated':True,'public_vacancy_list_modified':False}}
with open(art+'/source_scout.json','w',encoding='utf-8') as f: json.dump(out,f,ensure_ascii=False,indent=2); f.write('\n')
lines=['# Source Scout — '+cycle,'','Verdict: PASS_NO_NEW_SOURCES','','## Scope','','Exactly one mandatory Source Scout for the current cycle. No sibling stage was started; no public vacancy list was modified.','','## Result','',f"- Confirmed new sources: 0\n- Rejected candidates: {len(rejected)}\n- Duplicates: 0\n- Retired: 0\n- Active registry sources retained: {len(reg.get('sources',[]))}",'','## Backend evidence','','- Camofox: unavailable; CAMOFOX_URL unset in the actual worker environment.','- SearXNG: unavailable; SEARXNG_URL unset.','- Exa MCP: HTTP 429 free-tier rate limit.','- crawl4ai-skill: executable not found.','- Built-in web search: four German queries; no relevant new candidates.','- web_extract: backend timed out on candidate hosts.','- Direct HTTP/API: Jobgether 404, Jobicy 400; RemoteOK and Arbeitnow reachable but already registered; remaining candidates lacked two successful methods.','','## Rejected candidates','']
lines += [f"- {x['domain']}: {x['reason']}" for x in rejected]
lines += ['','## Registry decision','','No candidate met the requirement of a new independently searchable source verified by both a live direct vacancy card/accessibility listing/API and an independent second evidence method. Registry history was updated atomically; existing sources were retained.','']
with open(art+'/source_scout_report.md','w',encoding='utf-8') as f:f.write('\n'.join(lines))
print(art+'/source_scout.json',art+'/source_scout_report.md',reg['last_source_scout_cycle'])
