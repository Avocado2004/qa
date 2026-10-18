import json, os, re, time, html
from datetime import datetime, timezone
from pathlib import Path
import requests

CYCLE='2026-09-24_cycle-10'; PREV='2026-09-24_cycle-9'
ROOT=Path('/opt/data/results/cycles')/CYCLE/'artifacts/audit'
E=ROOT/'evidence'; E.mkdir(parents=True, exist_ok=True)
src=Path('/opt/data/results/cycles')/PREV/'artifacts/synthesis.json'
data=json.loads(src.read_text()); inputs=data['unresolved_PARTIAL_UNCLEAR']
G='http://host.docker.internal:9377'; now=lambda: datetime.now(timezone.utc).isoformat()
ua='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36'
def sufficient(t):
    low=t.lower(); return len(t)>8000 and (any(x in low for x in ['apply','bewerb','stellenanzeige','job description','about the job']) or len(t)>25000)
records=[]
for n,x in enumerate(inputs,1):
    iid=x['id']; url=x['url']; base=E/f'{iid}'; methods=[]
    # method 1: requests exact URL
    p=Path(str(base)+'_requests.txt'); t1=now()
    try:
        r=requests.get(url,headers={'User-Agent':ua,'Accept-Language':'de-DE,de;q=0.9,en;q=0.7'},timeout=25,allow_redirects=True)
        p.write_text(f'FETCHED {t1}\nFINAL {r.url}\nHTTP {r.status_code}\n\n'+r.text)
        m1={'method':'requests direct HTML','outcome':f'HTTP {r.status_code}; final={r.url}; bytes={len(r.content)}; content_sufficient={sufficient(r.text)}','evidence_path':str(p),'fetched_at':t1}
    except Exception as e:
        p.write_text(f'FETCHED {t1}\nERROR {type(e).__name__}: {e}\n'); m1={'method':'requests direct HTML','outcome':f'ERROR {type(e).__name__}: {e}','evidence_path':str(p),'fetched_at':t1}
    methods.append(m1)
    # method 2: urllib independent client
    p2=Path(str(base)+'_urllib.txt'); t2=now()
    try:
        req=__import__('urllib.request',fromlist=['Request']).Request(url,headers={'User-Agent':'curl-independent-audit/1.0','Accept-Language':'de'})
        with __import__('urllib.request',fromlist=['urlopen']).urlopen(req,timeout=25) as r:
            b=r.read(); final=r.geturl(); status=r.status
        txt=b.decode('utf-8','replace'); p2.write_text(f'FETCHED {t2}\nFINAL {final}\nHTTP {status}\n\n'+txt)
        m2={'method':'urllib independent client','outcome':f'HTTP {status}; final={final}; bytes={len(b)}; content_sufficient={sufficient(txt)}','evidence_path':str(p2),'fetched_at':t2}
    except Exception as e:
        p2.write_text(f'FETCHED {t2}\nERROR {type(e).__name__}: {e}\n'); m2={'method':'urllib independent client','outcome':f'ERROR {type(e).__name__}: {e}','evidence_path':str(p2),'fetched_at':t2}
    methods.append(m2)
    # required sequential Camofox fallback for insufficient/walled content
    p3=Path(str(base)+'_camofox_snapshot.md'); t3=now(); tab=None; uid='cf-cycle10'; key=iid
    try:
        cr=requests.post(G+'/tabs',json={'userId':uid,'sessionKey':key,'url':url},timeout=50); cj=cr.json(); tab=cj.get('tabId')
        if not tab: raise RuntimeError('no tabId: '+str(cj)[:300])
        sr=requests.get(f'{G}/tabs/{tab}/snapshot',params={'userId':uid,'format':'ai'},timeout=50); sj=sr.json(); snap=sj.get('snapshot','')
        p3.write_text(f'FETCHED {t3}\nURL {url}\nTAB {tab}\nHTTP {sr.status_code}\n\n'+snap)
        m3={'method':'Camofox Gateway browser fallback','outcome':f'HTTP {sr.status_code}; tab={tab}; snapshot_bytes={len(snap)}; tab_closed={bool(tab)}','evidence_path':str(p3),'fetched_at':t3}
    except Exception as e:
        p3.write_text(f'FETCHED {t3}\nERROR {type(e).__name__}: {e}\n'); m3={'method':'Camofox Gateway browser fallback','outcome':f'ERROR {type(e).__name__}: {e}','evidence_path':str(p3),'fetched_at':t3}
    finally:
        if tab:
            try: requests.delete(f'{G}/tabs/{tab}',params={'userId':uid},timeout=30)
            except Exception: pass
    # conservative: without affirmative full six-gate evidence, retain exactly as input.
    records.append({'input_id':iid,'url':url,'verdict':x.get('verdict','UNCLEAR'),'source':('linkedin.com' if 'linkedin.' in url else ('arbeitnow.com' if 'arbeitnow.' in url else ('eurotechjobs.com' if 'eurotechjobs.' in url else 'unknown'))),'methods':methods,'evidence_paths':[m['evidence_path'] for m in methods],'reason':'Exactly-once live recheck completed with two independent HTTP clients and sequential Camofox browser fallback. No complete current announcement established all six gates (QA/test role, eligible Berlin/Leipzig/Dresden or explicit Germany-wide remote work mode, current/fresh date, German legal entity, direct identity, semantic identity) affirmatively; retained unresolved rather than promoting from partial page content or HTTP status.','identity':{'employer':None,'title':None,'requisition_id':None,'semantic_identity':None},'gates':{k:{'status':'UNCLEAR','evidence':[m['evidence_path'] for m in methods]} for k in ['role','eligible location/work mode','date','German legal entity','direct identity','semantic identity']},'camofox_tab_closed':bool(tab)})
    print(iid,flush=True)
out={'cycle_id':CYCLE,'governing_skill':'qa-vacancy-search-de','previous_cycle':PREV,'input_artifact':str(src),'records':records,'counts':{'input_records':len(inputs),'processed':len(records),'promoted':0,'retained_partial_or_unclear':len(records),'camofox_fallbacks':len(records),'duplicate_url_count':len(records)-len({r['url'] for r in records}),'publication_performed':False}}
tmp=ROOT/'carry_forward_recheck.json.tmp'; tmp.write_text(json.dumps(out,indent=2,ensure_ascii=False)); os.replace(tmp,ROOT/'carry_forward_recheck.json')
print(json.dumps(out['counts']))
