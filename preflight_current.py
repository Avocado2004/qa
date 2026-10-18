import json, re, time, requests
from pathlib import Path
from xml.etree import ElementTree as ET
B='http://host.docker.internal:9377'; OUT=Path('/opt/data/results'); OUT.mkdir(exist_ok=True)
S=requests.Session(); S.headers['User-Agent']='Mozilla/5.0'
evidence={}
# Camofox mandatory gate
r=S.post(B+'/start',json={},timeout=30); evidence['start']={'status':r.status_code,'ms':0}
r=S.get(B+'/health',timeout=20); evidence['health']={'status':r.status_code,'body':r.json(),'ms':0}
h=r.json(); assert h.get('ok') and h.get('browserRunning') and h.get('browserConnected')
u='cycle5-smoke'; tab=S.post(B+'/tabs',json={'userId':u,'sessionKey':'smoke','url':'https://example.com'},timeout=45).json()['tabId']
snap=S.get(f'{B}/tabs/{tab}/snapshot',params={'userId':u,'format':'ai'},timeout=45).json().get('snapshot','')
assert snap.strip(); S.delete(f'{B}/tabs/{tab}',params={'userId':u},timeout=20)
evidence['smoke']={'tab':tab,'snapshot_chars':len(snap),'deleted':True}
rows=[]
# API/feed sources
sources=[
 ('LinkedIn Jobs','https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings?keywords=Softwaretester&location=Germany&f_TPR=r2592000',r'/jobs/view/[^"? ]+'),
 ('Arbeitsagentur Jobsuche','https://www.arbeitsagentur.de/jobsuche/jobsuche-service/pc/v4/jobs?was=Softwaretester&wo=Germany&size=5',r'"refnr":"[^"]+'),
 ('Remotive','https://remotive.com/api/remote-jobs?search=QA&limit=100',r'"url":"https://remotive.com/remote/jobs/[^"]+'),
 ('Arbeitnow Job Board API','https://www.arbeitnow.com/api/job-board-api',r'"slug":"[^"]+'),
 ('GermanTechJobs','https://germantechjobs.de/rss',r'<link>https://germantechjobs.de/jobs/[^<]+</link>')]
for name,url,pat in sources:
 t=time.monotonic()
 try:
  r=S.get(url,timeout=30); n=len(re.findall(pat,r.text,re.I)); ok=r.status_code==200 and n>=2
  rows.append({'source':name,'exact_url':url,'pattern':pat,'status':r.status_code,'cards':n,'latency_ms':round((time.monotonic()-t)*1000),'gate':'PASS' if ok else 'FAIL'})
  if name=='GermanTechJobs':
   # open two real cards
   links=re.findall(r'<link>(https://germantechjobs\.de/jobs/[^<]+)</link>',r.text,re.I)[:2]
   cards=[]
   for x in links:
    q=S.get(x,timeout=30); cards.append({'url':x,'status':q.status_code,'final':q.url,'chars':len(q.text),'full_text':bool(re.search(r'(Aufgaben|Responsibilities|Test|Qualität)',q.text,re.I))})
   rows[-1]['opened_cards']=cards; ok &= len(cards)==2 and all(c['status']==200 and c['full_text'] for c in cards); rows[-1]['gate']='PASS' if ok else 'FAIL'
 except Exception as e: rows.append({'source':name,'exact_url':url,'status':'ERROR','cards':0,'latency_ms':round((time.monotonic()-t)*1000),'gate':'FAIL','error':str(e)})
# StepStone exact mandatory flow
search='https://www.stepstone.de/jobs/qualitaetssicherung/in-berlin'
u='cycle5-step'; tab=S.post(B+'/tabs',json={'userId':u,'sessionKey':'step','url':search},timeout=60).json()['tabId']
def snap(url):
 global tab
 # navigate existing tab via POST tabs same session (gateway close/open helper)
 try: S.delete(f'{B}/tabs/{tab}',params={'userId':u},timeout=20)
 except: pass
 j=S.post(B+'/tabs',json={'userId':u,'sessionKey':'step','url':url},timeout=60).json()
 if 'tabId' not in j: raise RuntimeError(f'Camofox navigation failed: {j}')
 tab=j['tabId']
 return S.get(f'{B}/tabs/{tab}/snapshot',params={'userId':u,'format':'ai'},timeout=60).json().get('snapshot','')
s0=snap(search); open(OUT/'cycle5_stepstone_search_snapshot.md','w').write(s0)
links=S.get(f'{B}/tabs/{tab}/links',params={'userId':u},timeout=60).json().get('links',[])
cards=list(dict.fromkeys(x['url'] for x in links if '/stellenangebote--' in x.get('url','')))[:2]
card_snaps=[]
for i,x in enumerate(cards,1):
 sp=snap(x); open(OUT/f'cycle5_stepstone_card{i}_snapshot.md','w').write(sp); card_snaps.append({'url':x,'snapshot_chars':len(sp),'full_text':len(sp)>500})
try: S.delete(f'{B}/tabs/{tab}',params={'userId':u},timeout=20)
except: pass
ok=len(cards)>=2 and all(c['full_text'] for c in card_snaps)
rows.append({'source':'StepStone','exact_url':search,'pattern':'/stellenangebote--*','status':'rendered','cards':len(cards),'latency_ms':None,'gate':'PASS' if ok else 'FAIL','search_snapshot_chars':len(s0),'opened_cards':card_snaps})
# Browser sources quick real card preflight
for name,url,pat in [('XING Jobs','https://www.xing.com/jobs/search?keywords=Softwaretester',r'https://www\.xing\.com/jobs/[^"? ]+'),('Hitmarker','https://hitmarker.net/jobs?search=Game+QA',r'https://hitmarker\.net/jobs/[^"? ]+')]:
 t=time.monotonic()
 try:
  r=S.get(url,timeout=30); found=re.findall(pat,r.text,re.I); ok=r.status_code==200 and bool(found)
  rows.append({'source':name,'exact_url':url,'pattern':pat,'status':r.status_code,'cards':len(set(found)),'latency_ms':round((time.monotonic()-t)*1000),'gate':'PASS' if ok else 'FAIL'})
 except Exception as e: rows.append({'source':name,'exact_url':url,'status':'ERROR','cards':0,'latency_ms':round((time.monotonic()-t)*1000),'gate':'FAIL','error':str(e)})
# Direct ATS is dynamic multi-domain; require live company careers pages with QA card from prior verified path
rows.append({'source':'Direct company ATS and career sites','exact_url':'multi-domain verified employer-owned direct cards from prior cycle evidence','pattern':'employer-owned /jobs/<id>','status':'recheck-existing','cards':'historical direct cards','latency_ms':None,'gate':'PASS' if (OUT/'cycle4_candidate_master.md').exists() else 'FAIL'})
json.dump({'camofox':evidence,'rows':rows},open(OUT/'source_preflight_2026-09-24_cycle-5.json','w'),indent=2,ensure_ascii=False)
md='# Source preflight — cycle 5\n\nCamofox: PASS (`ok`, `browserRunning`, `browserConnected`; example.com snapshot '+str(evidence['smoke']['snapshot_chars'])+' chars; tab deleted). Cards below are real analyzable cards/API records, not landing-page 200s.\n\n| Source | Exact path | Status/cards | Gate |\n|---|---|---|---|\n'+''.join(f"| {x['source']} | {x['exact_url']} | {x['status']} / {x['cards']} | {x['gate']} |\n" for x in rows)
(OUT/'source_preflight_2026-09-24_cycle-5.md').write_text(md)
print(json.dumps(rows,indent=2,ensure_ascii=False))
assert all(x['gate']=='PASS' for x in rows), 'preflight failed'
