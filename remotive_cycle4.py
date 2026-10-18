import json, urllib.parse, urllib.request, time, re, html, os
from pathlib import Path
from datetime import datetime
OUT=Path('/opt/data/results/vac-2026-09-24-source-07-cycle-4'); RAW=OUT/'raw'; RAW.mkdir(parents=True,exist_ok=True)
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36'
def fetch(url, name, headers=None):
    t=time.time(); req=urllib.request.Request(url,headers=headers or {'User-Agent':UA,'Accept-Language':'de-DE,de;q=0.9,en;q=0.8'})
    try:
        with urllib.request.urlopen(req,timeout=30) as r: b=r.read(); st=r.status; final=r.geturl()
        (RAW/name).write_bytes(b); return {'url':url,'status':st,'final':final,'ms':round((time.time()-t)*1000),'bytes':len(b)}
    except Exception as e:
        return {'url':url,'status':'ERROR','error':str(e),'ms':round((time.time()-t)*1000)}
coverage=[]; alljobs={}
# sequential public API axes: location and role
for loc in ['Berlin','Leipzig','Dresden','Germany-wide Remote']:
  for role in ['Manual WEB QA','Software Test / Automation','Gamedev QA','Other QA Roles']:
    q=role + ' ' + loc
    u='https://remotive.com/api/remote-jobs?'+urllib.parse.urlencode({'search':q,'limit':100})
    r=fetch(u,re.sub(r'[^a-z0-9]+','_',loc+'_'+role).strip('_')+'.json',{'User-Agent':'curl/8.5','Accept':'application/json'})
    try:
      d=json.loads((RAW/re.sub(r'[^a-z0-9]+','_',loc+'_'+role).strip('_')+'.json').read_text())
      jobs=d.get('jobs',[]); alljobs.update({j.get('url'):j for j in jobs if j.get('url')})
      r['cards']=len(jobs)
    except Exception: r['cards']=0
    coverage.append({'surface':'public API','location_axis':loc,'role_axis':role,'query':u,**r})
# category and direct card inventory sequentially
r=fetch('https://remotive.com/remote-jobs/qa','remotive_qa_category.html'); coverage.append({'surface':'QA category','location_axis':'all','role_axis':'all','query':r['url'],**r})
# fetch all API unique direct cards, sequentially (full announcement)
for i,(url,j) in enumerate(alljobs.items(),1):
  time.sleep(.25); d=fetch(url,f'direct_{i:03d}.html'); d.update({'surface':'direct card','title':j.get('title'),'url_card':url,'query':'API result'}); coverage.append(d)
  if d.get('status')==200: j['_direct_status']=d['status']
(OUT/'coverage.json').write_text(json.dumps(coverage,indent=2,ensure_ascii=False))
(OUT/'api_jobs.json').write_text(json.dumps(list(alljobs.values()),indent=2,ensure_ascii=False))
print(json.dumps({'api_unique':len(alljobs),'coverage':len(coverage),'out':str(OUT)}))
