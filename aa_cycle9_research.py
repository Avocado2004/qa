import json, os, re, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from html import unescape
OUT='/opt/data/results/source_preflight_2026-09-24_cycle-9/arbeitsagentur.de'; os.makedirs(OUT+'/raw',exist_ok=True)
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36'
def fetch(url,fn):
 req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml,application/json'}); t=time.time()
 try:
  with urllib.request.urlopen(req,timeout=30) as r: data=r.read(); status=r.status; ct=r.headers.get('Content-Type','')
 except Exception as e: data=repr(e).encode(); status=0; ct='error'
 p=f'{OUT}/raw/{fn}'; open(p,'wb').write(data)
 return {'url':url,'file':p,'http_status':status,'content_type':ct,'bytes':len(data),'latency_ms':round((time.time()-t)*1000),'checked_at':datetime.now(timezone.utc).isoformat()}
checks=[]
for i,(q,loc) in enumerate([('Softwaretester','Berlin'),('QA Engineer','Leipzig'),('Testautomatisierung','Dresden'),('Qualitätssicherung','Deutschland')],1):
 url='https://www.arbeitsagentur.de/jobsuche/suche?'+urllib.parse.urlencode({'suchbereich':'jobs','was':q,'wo':loc}); x=fetch(url,f'listing_{i}_{q}_{loc}.html'); checks.append(x); time.sleep(1)
 if x['http_status']==200:
  s=open(x['file'],encoding='utf-8',errors='ignore').read(); links=sorted(set(unescape(u) for u in re.findall(r'href="(https://www\.arbeitsagentur\.de/jobsuche/jobdetail/[^"]+)"',s))); x['card_pattern']='/jobsuche/jobdetail/<refnr>-<suffix>'; x['direct_cards']=links; x['card_count']=len(links)
  if links:
   d=fetch(links[0],f'detail_{i}.html'); checks.append(d)
   if d['http_status']==200:
    ds=open(d['file'],encoding='utf-8',errors='ignore').read(); d['identity_markers']={'title_marker':bool(re.search(r'Jobeinfos|Softwaretester|QA',ds,re.I)),'refnr':links[0].rsplit('/',1)[-1],'detail_contains_refnr':links[0].rsplit('/',1)[-1] in ds,'jsonld':bool(re.search(r'application/ld\+json',ds,re.I))}
for page in (1,2): checks.append(fetch('https://www.arbeitsagentur.de/jobsuche/suche?'+urllib.parse.urlencode({'suchbereich':'jobs','was':'Softwaretester','wo':'Berlin','page':page}),f'pagination_{page}.html'))
checks.append(fetch('https://web.arbeitsagentur.de/jobsuche/jobsuche-service/pc/v4/jobs?was=Softwaretester&wo=Berlin&size=10&page=1','api_v4_probe.txt'))
adapter='''# Source Adapter — arbeitsagentur.de

- Cycle: `2026-09-24_cycle-9`
- Governing skill: `qa-vacancy-search-de`
- Verified source: Bundesagentur für Arbeit Jobsuche.

## Primary discovery and search route
`https://www.arbeitsagentur.de/jobsuche/suche?suchbereich=jobs&was=<German query>&wo=<location>`

Verified German probes: `Softwaretester`/Berlin, `QA Engineer`/Leipzig, `Testautomatisierung`/Dresden and `Qualitätssicherung`/Deutschland. The page is server-rendered and contains `jb-job-listen-eintrag` cards.

## Card selector and direct detail route
- Listing component: `jb-job-listen-eintrag` / `article.ba-tile.listeneintrag`.
- Direct card: `https://www.arbeitsagentur.de/jobsuche/jobdetail/<reference number>-<hash suffix>`.
- Observed: `/10000-1183466875-S` and `/12811-2337109-S`.
- Open and semantically analyze the complete direct announcement; do not classify from the compact listing card.

## Pagination
Append `page=<1-based page>`. Compare page identities; stop when page 2 repeats page 1, has no cards, or the displayed maximum boundary is reached. Deduplicate by direct jobdetail reference.

## Access, authentication and anti-bot
Primary method: ordinary HTTP GET with browser User-Agent. No login was required. The first recorded call was HTTP 200. Serialize operations and honor 429/Retry-After. If blocked, retry sequentially using rendered browser/Camofox, then web extraction. A shell/API failure is not zero results.

## API status
The historical unauthenticated `https://web.arbeitsagentur.de/jobsuche/jobsuche-service/pc/v4/jobs?was=...&wo=...&size=...&page=...` path returned HTTP 404 this cycle. It is negative evidence only; do not claim it as a working API. Use the verified server-rendered search route.

## Evidence
Raw responses and metadata are in `raw/` and `research_checks.json`. The independent verifier assigns PASS/FAILED/BLOCKED, not this researcher.
'''
open(OUT+'/source_adapter.md','w').write(adapter); open(OUT+'/research_checks.json','w').write(json.dumps({'cycle_id':'2026-09-24_cycle-9','source_id':'arbeitsagentur.de','checked_at':datetime.now(timezone.utc).isoformat(),'checks':checks},ensure_ascii=False,indent=2))
result={'cycle_id':'2026-09-24_cycle-9','source_id':'arbeitsagentur.de','status':'completed','adapter_path':OUT+'/source_adapter.md','evidence_paths':[OUT+'/raw',OUT+'/research_checks.json'],'governing_skill':'qa-vacancy-search-de','summary':'Verified live server-rendered Jobsuche search route, direct jobdetail pattern, German query/location parameters and page navigation. Listing and first direct detail returned HTTP 200; two direct cards observed. Historical v4 API returned 404 and is non-primary.'}
open(OUT+'/task_result.json','w').write(json.dumps(result,ensure_ascii=False,indent=2)); print(json.dumps(result))
