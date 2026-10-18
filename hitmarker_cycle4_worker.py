import json, os, time, urllib.parse, urllib.request
from pathlib import Path
BASE=Path('/opt/data/results/vac-2026-09-24-source-05-cycle-4'); BASE.mkdir(parents=True,exist_ok=True)
CAMO=os.environ.get('CAMOFOX_URL','http://host.docker.internal:9377').rstrip('/')
USER='hitmarker-cycle4'; SKEY='hitmarker-cycle4-sequential'
def req(path, method='GET', body=None):
    data=None if body is None else json.dumps(body).encode()
    r=urllib.request.Request(CAMO+path,data=data,method=method,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(r,timeout=60) as x: return json.loads(x.read() or '{}')
def snap(tab,name):
    x=req(f'/tabs/{tab}/snapshot?userId={USER}&format=accessibility')
    text=x.get('snapshot') or x.get('text') or x.get('content') or json.dumps(x,ensure_ascii=False)
    (BASE/name).write_text(text)
    return text
req('/start','POST',{})
t=req('/tabs','POST',{'userId':USER,'sessionKey':SKEY,'url':'https://hitmarker.net/game-tester-jobs'})
tab=t.get('tabId') or t.get('id')
req(f'/tabs/{tab}/wait', 'POST', {'userId':USER,'selector':'body','timeout':15000})
smoke=snap(tab,'evidence_00_smoke.md')
# role families intersect Hitmarker's game/QA vertical, each searched across all required axes
roles=['Quality Assurance']
locs=['Germany Remote']
log=[]
try:
    n=12
    for ri,role in enumerate(roles,4):
        for li,loc in enumerate(locs,4):
            n+=1
            q=role if loc=='Germany Remote' else f'{role} {loc}'
            url='https://hitmarker.net/game-tester-jobs?search='+urllib.parse.quote_plus(q)
            nr=req(f'/tabs/{tab}/navigate','POST',{'userId':USER,'url':url,'timeout':30000})
            try: req(f'/tabs/{tab}/wait','POST',{'userId':USER,'selector':'body','timeout':10000})
            except Exception: pass
            text=snap(tab,f'evidence_{ri}_{li}_{role.lower().replace(" ","_")}_{loc.lower().replace(" ","_")}.md')
            log.append({'order':n,'role_axis':role,'location_axis':loc,'query':q,'url':url,'snapshot_chars':len(text),'direct_cards':len(set(__import__('re').findall(r'https?://hitmarker\.net/jobs/[a-z0-9-]+',text)))})
    (BASE/'evidence_query_matrix.json').write_text(json.dumps(log,indent=2,ensure_ascii=False))
finally:
    req(f'/tabs/{tab}?userId={USER}','DELETE')
print(json.dumps({'tab':tab,'queries':len(log),'chars':sum(x['snapshot_chars'] for x in log),'cards':sum(x['direct_cards'] for x in log)}))
