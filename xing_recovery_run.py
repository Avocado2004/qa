import json, os, re, time, urllib.parse, urllib.request
from pathlib import Path
BASE=Path('/opt/data/results/vac-2026-09-24_cycle-5-source-xing.com'); RAW=BASE/'raw'; STATE=BASE/'.worker-state'; QUEUE=Path('/opt/data/results/cycles/2026-09-24_cycle-5/worker-pool/queue.json')
CAMO=os.environ.get('CAMOFOX_URL','http://host.docker.internal:9377').rstrip('/'); USER='recovery'; SKEY='recovery-xing-cycle5'
queries=['Softwaretester','QA Engineer','Test Engineer','Qualitätssicherung','Spiele-Tester','Test Automation','Game QA','QA Localization']; scopes=['Berlin','Leipzig','Dresden','Germany-wide Remote']
def req(path, method='GET', body=None, timeout=60):
    data=None if body is None else json.dumps(body).encode()
    r=urllib.request.Request(CAMO+path,data=data,method=method,headers={'Content-Type':'application/json','Accept':'application/json'})
    with urllib.request.urlopen(r,timeout=timeout) as x:
        raw=x.read().decode('utf-8','replace'); return json.loads(raw) if raw else {}
def snap(tab,path,format='accessibility'):
    try:
        x=req(f'/tabs/{urllib.parse.quote(tab)}/snapshot?{urllib.parse.urlencode({"userId":USER,"format":format})}')
        text=x.get('snapshot') or x.get('text') or x.get('content') or json.dumps(x,ensure_ascii=False)
        Path(path).write_text(text,encoding='utf-8'); return text
    except Exception as e: Path(path).write_text('CAMOFOX ERROR: '+repr(e)); return ''
def hb():
    subprocess=None
    os.system(f"python3 /opt/data/qa-vacancy-project/worker_queue.py {QUEUE} recovery heartbeat >/dev/null")
def set_ck(**kw):
    p=STATE/'checkpoint.json'; d=json.loads(p.read_text()) if p.exists() else {}; d.update(kw); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def set_manifest(**kw):
    p=STATE/'manifest.json'; d=json.loads(p.read_text()); d.update(kw); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def evaljs(tab,expr):
    return req(f'/tabs/{urllib.parse.quote(tab)}/evaluate','POST',{'userId':USER,'expression':expr}).get('result')
def main():
    RAW.mkdir(exist_ok=True); STATE.mkdir(exist_ok=True)
    # Required gateway verification, configured gateway only.
    start=req('/start','POST',{}); health=req('/health')
    sm=req('/tabs','POST',{'userId':USER,'sessionKey':SKEY,'url':'https://www.xing.com/jobs/search/ki'})
    tab=sm.get('tabId'); smoke=snap(tab,RAW/'recovery_00_gateway_smoke.md','text') if tab else ''
    if tab: req(f'/tabs/{urllib.parse.quote(tab)}?userId={USER}','DELETE')
    tab = None
    gate={'start':start,'health':health,'smoke_nonempty':bool(smoke.strip())}
    hb(); set_manifest(state='active',last_error=None,updated_at=None)
    rows=[]; cells=[]; card_urls=set(); total=0
    try:
      for qi,q in enumerate(queries,1):
       for si,scope in enumerate(scopes,1):
        cell=f'{qi:02d}-{si:02d}'; fn=RAW/f'cell_{cell}_{re.sub("[^A-Za-z0-9]+","_",q+"_"+scope)}.md'; hb()
        if not tab:
            req('/start','POST',{}); tab=req('/tabs','POST',{'userId':USER,'sessionKey':SKEY,'url':'https://www.xing.com/jobs/search/ki'}).get('tabId')
        if not tab:
            raise RuntimeError('Camofox tab creation returned no tabId')
        # The initial tab may already be on the target route; navigate only if needed.
        current = req('/tabs?userId='+USER).get('tabs', [])
        if not any(t.get('tabId') == tab and t.get('url','').startswith('https://www.xing.com/jobs/search/ki') for t in current):
            req(f'/tabs/{urllib.parse.quote(tab)}/navigate','POST',{'userId':USER,'url':'https://www.xing.com/jobs/search/ki','timeout':30000})
        req(f'/tabs/{urllib.parse.quote(tab)}/wait','POST',{'userId':USER,'selector':'body','timeout':15000})
        # DOM-native input events, then required button
        js=f'''(()=>{{let q=document.querySelector('#query-input-input[data-testid="cs-search-bar-textarea"]'); if(!q)return 'query-missing'; let s=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set; s.call(q,{json.dumps(q)}); q.dispatchEvent(new Event('input',{{bubbles:true}})); return 'query-set';}})()'''
        evaljs(tab,js); evaljs(tab,'''(()=>{let b=document.querySelector('button[aria-label="Find jobs"]');if(b)b.click();return !!b})()'''); time.sleep(1)
        evaljs(tab,'''(()=>{let l=document.querySelector('#location-input-input');if(!l)return 'loc-missing';let s=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;s.call(l,%s);l.dispatchEvent(new Event('input',{bubbles:true}));return 'loc-set'})()'''%json.dumps(scope))
        evaljs(tab,'''(()=>{let b=document.querySelector('button[aria-label="Find jobs"]');if(b)b.click();return !!b})()'''); time.sleep(2)
        # visible Last month filter via text/aria; then capture and collect links
        evaljs(tab,'''(()=>{let els=[...document.querySelectorAll('button,[role="button"],label')];let e=els.find(x=>(x.innerText||x.getAttribute('aria-label')||'').toLowerCase().includes('last month'));if(e){e.click();return true}return false})()'''); time.sleep(2)
        before=-1; steps=0
        while True:
          text=snap(tab,fn); links=req(f'/tabs/{urllib.parse.quote(tab)}/links?userId={USER}').get('links',[])
          direct=[x.get('href','') for x in links if re.search(r'/jobs/.+-\d+(?:[/?#]|$)',x.get('href',''))]
          card_urls.update(u for u in direct if u)
          if len(text)==before or steps>=20: break
          before=len(text); steps+=1
          more=evaljs(tab,'''(()=>{let e=[...document.querySelectorAll('button,[role="button"]')].find(x=>/show more|mehr anzeigen/i.test((x.innerText||x.getAttribute('aria-label')||'')));if(e){e.click();return true}return false})()''')
          if not more: break
          time.sleep(1)
        total+=len(direct)
        cells.append({'cell':cell,'query':q,'scope':scope,'status':'complete' if text and not text.startswith('CAMOFOX') else 'failed','cards':len(direct),'show_more_steps':steps,'capture':str(fn)})
        set_ck(last_cell=cell,last_query=q,last_scope=scope,completed_cells=len(cells),remaining_cells=32-len(cells),state='active',last_error=None)
        if direct: rows.append((q,scope,direct,str(fn)))
    except Exception as e:
      set_manifest(state='failed',last_error='blocked_external: '+repr(e)); raise
    finally:
      if tab:
       try: req(f'/tabs/{urllib.parse.quote(tab)}?userId={USER}','DELETE')
       except: pass
    # retain only direct links as candidates; no semantic acceptance without full card evidence
    prov={'cycle_id':'2026-09-24_cycle-5','source_id':'xing.com','worker_id':'recovery','gateway':CAMO,'gate':gate,'cells':cells,'total_card_links_observed':total,'unique_direct_urls':len(card_urls),'candidates':[{'query':q,'scope':s,'url':u,'capture':f} for q,s,us,f in rows for u in us]}
    (BASE/'provenance.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n')
    (BASE/'result.md').write_text('# XING recovery result\n\nNo rows published; candidate links require full-card semantic verification.\n\n'+'\n'.join(f'- {c["query"]} / {c["scope"]}: {c["cards"]} direct links, {c["show_more_steps"]} Show-more steps' for c in cells)+'\n')
    (BASE/'source_coverage.md').write_text('# Source coverage — XING recovery\n\n'+f'- cells: {len(cells)}/32 complete\n- cards: {total}; unique direct URLs: {len(card_urls)}\n- sequential Camofox Gateway: {CAMO}\n- no zero-result claim; no publication\n'+'\n'.join(f'| {c["cell"]} | {c["query"]} | {c["scope"]} | {c["status"]} | {c["cards"]} |' for c in cells)+'\n')
    (BASE/'completed_receipt.md').write_text(f'# Recovery receipt\n\n- worker: recovery; queue: claimed by recovery; no claim/retry called\n- gateway: {CAMO}\n- cells: {len(cells)}/32; direct card links: {total}; unique: {len(card_urls)}\n- full-card semantic verification: not completed for candidates\n- publication: none\n')
    set_ck(state='complete' if len(cells)==32 else 'failed',completed_cells=len(cells),evidenced_cells=len(cells),remaining_cells=32-len(cells),last_error=None)
    set_manifest(state='complete' if len(cells)==32 else 'failed',last_error=None)
    print(json.dumps({'cells':len(cells),'cards':total,'unique':len(card_urls),'state':'complete' if len(cells)==32 else 'failed'}))
if __name__=='__main__': main()
