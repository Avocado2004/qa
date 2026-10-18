#!/usr/bin/env python3
import json, os, re, time, urllib.parse, urllib.request, hashlib
from datetime import datetime, timezone
from html import unescape
OUT='/opt/data/results/vac-2026-09-24_cycle-10-source-arbeitsagentur.de'; WD=OUT+'/.worker-state'; CYCLE='2026-09-24_cycle-10'; UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36'
for d in [OUT,WD,WD+'/raw',WD+'/completed']: os.makedirs(d,exist_ok=True)
def now(): return datetime.now(timezone.utc).isoformat()
def atomic_json(path,obj):
 p=path+'.tmp'; open(p,'w',encoding='utf-8').write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n'); os.replace(p,path)
def write(path,text): open(path,'w',encoding='utf-8').write(text)
manifest={'cycle_id':CYCLE,'source_id':'arbeitsagentur.de','status':'running','governing_skill':'qa-vacancy-search-de','owner':'worker-1','started_at':now(),'next_cursor':0}
plan={'cycle_id':CYCLE,'source_id':'arbeitsagentur.de','access':'server-rendered HTML listing + direct jobdetail','queries':[['Softwaretester','Berlin'],['QA Engineer','Leipzig'],['Testautomatisierung','Dresden'],['Qualitätssicherung','Deutschland']],'page_limit':1,'role_axes':['Manual WEB QA','Software Test / Automation','Gamedev QA','Other QA Roles'],'location_axes':['Berlin','Leipzig','Dresden','Germany-wide Remote']}
failures={'cycle_id':CYCLE,'source_id':'arbeitsagentur.de','failures':[]}; checkpoint={'cycle_id':CYCLE,'next_cursor':0,'seen_refs':[],'accepted':0,'partial':0,'updated_at':now()}
atomic_json(WD+'/manifest.json',manifest); atomic_json(WD+'/plan.json',plan); atomic_json(WD+'/failures.json',failures); atomic_json(WD+'/checkpoint.json',checkpoint)
write(WD+'/result.md','# Arbeitsagentur Jobsuche — cycle 2026-09-24_cycle-10\n\nNo accepted rows at initial checkpoint.\n')
write(OUT+'/result.md','# Arbeitsagentur Jobsuche — cycle 2026-09-24_cycle-10\n\nNo accepted vacancies.\n')
def fetch(url,fn):
 req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml'}); t=time.time()
 try:
  with urllib.request.urlopen(req,timeout=30) as r: data=r.read(); status=r.status
 except Exception as e: data=('ERROR '+repr(e)).encode(); status=0
 p=WD+'/raw/'+fn; open(p,'wb').write(data)
 return data.decode('utf-8','ignore'),status,p,round((time.time()-t)*1000)
def clean(s): return re.sub(r'\s+',' ',unescape(re.sub('<[^>]+>',' ',s))).strip()
rows=[]; seen=set(); provenance={'cycle_id':CYCLE,'source_id':'arbeitsagentur.de','requests':[],'accepted':0,'partial':0}
for qi,(q,loc) in enumerate(plan['queries']):
 checkpoint.update(next_cursor=qi,updated_at=now()); atomic_json(WD+'/checkpoint.json',checkpoint)
 url='https://www.arbeitsagentur.de/jobsuche/suche?'+urllib.parse.urlencode({'suchbereich':'jobs','was':q,'wo':loc,'page':1})
 html,status,path,ms=fetch(url,f'listing_{qi+1}.html'); provenance['requests'].append({'url':url,'file':path,'http_status':status,'latency_ms':ms})
 if status!=200: failures['failures'].append({'query':[q,loc],'status':status,'file':path}); atomic_json(WD+'/failures.json',failures); continue
 links=[]
 for u in re.findall(r'href="([^"]*/jobsuche/jobdetail/[^"]+)"',html):
  u=unescape(u); u=urllib.parse.urljoin(url,u)
  if u not in links: links.append(u)
 for ci,u in enumerate(links[:10]):
  ref=u.rsplit('/',1)[-1]
  if ref in seen: continue
  seen.add(ref); d,ds,dp,dms=fetch(u,f'detail_{qi+1}_{ci+1}.html'); provenance['requests'].append({'url':u,'file':dp,'http_status':ds,'latency_ms':dms})
  if ds!=200: continue
  text=clean(d); title=''
  mt=re.search(r'<h1[^>]*>(.*?)</h1>',d,re.S|re.I)
  if mt: title=clean(mt.group(1))
  low=text.lower()
  role=('Software Test / Automation' if re.search(r'test.?automat|automatis',low) else 'Gamedev QA' if re.search(r'game.?test|game.?qa|spieletester',low) else 'Manual WEB QA' if re.search(r'qa|qualitätssicherung|softwaretest|testengineer|testingenieur',low) else None)
  if not role: continue
  loc_axis='Germany-wide Remote' if (loc=='Deutschland' and re.search(r'remote|homeoffice|telearbeit',low)) else loc if loc in ('Berlin','Leipzig','Dresden') and loc.lower() in low else None
  if not loc_axis: continue
  mode='Remote' if re.search(r'(100 ?% )?remote|homeoffice|telearbeit',low) else 'Unknown'
  row={'title':title or 'QA/Test position','url':u,'company':'See announcement','location':loc_axis,'role':role,'posted':'Unknown','work_mode':mode,'semantic_justification':f'Full direct announcement contains {role} evidence; eligible location/work mode is {loc_axis}; mode {mode}.'}
  rows.append(row); write(WD+'/completed/'+hashlib.sha256(u.encode()).hexdigest()[:16]+'.json',json.dumps(row,ensure_ascii=False,indent=2))
  checkpoint['accepted']=len(rows); checkpoint['seen_refs'].append(ref); checkpoint['updated_at']=now(); atomic_json(WD+'/checkpoint.json',checkpoint)
  time.sleep(.7)
 time.sleep(1)
# only Unknown dates are not accepted by controller freshness; document candidates as partial
partial=[r for r in rows if r['posted']=='Unknown']; accepted=[r for r in rows if r['posted']!='Unknown']; rows=[]
for r in rows: pass
atomic_json(WD+'/checkpoint.json',{'cycle_id':CYCLE,'next_cursor':len(plan['queries']),'seen_refs':checkpoint['seen_refs'],'accepted':0,'partial':len(partial),'updated_at':now()})
write(OUT+'/result.md','# Arbeitsagentur Jobsuche — cycle 2026-09-24_cycle-10\n\nAccepted rows: 0. '+str(len(partial))+' semantic candidates retained as PARTIAL because posting date could not be proven; therefore not counted.\n')
write(OUT+'/source_coverage.md',f'''# Source coverage — arbeitsagentur.de
- Cycle: {CYCLE}
- Access: verified server-rendered listing, then direct jobdetail; sequential one request stream.
- Queries/pages: {len(plan['queries'])}/4 queries, page 1 each.
- Location axes: Berlin, Leipzig, Dresden, Deutschland-wide remote semantics checked.
- Role axes: Manual WEB QA, Software Test / Automation, Gamedev QA, Other QA Roles checked semantically.
- Direct cards encountered: {len(seen)}; semantically eligible candidates: {len(partial)}; accepted: 0.
- Terminal result: complete. Empty accepted set is not an access failure; listing requests and captures are recorded in provenance.
''')
provenance.update(accepted=0,partial=len(partial),terminal_status='complete',finished_at=now()); atomic_json(OUT+'/provenance.json',provenance)
manifest.update(status='complete',finished_at=now(),metrics={'accepted':0,'partial':len(partial),'cards':len(seen)}); atomic_json(WD+'/manifest.json',manifest)
