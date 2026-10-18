#!/usr/bin/env python3
import re, json, subprocess, pathlib, html, urllib.parse, datetime, concurrent.futures
BASE=pathlib.Path('/opt/data/qa-vacancy-project')
master=BASE/'qa_vacancies_master_2026-09-24.md'
out=BASE/'old105_live_fetch.json'
lines=master.read_text(encoding='utf-8').splitlines()
section=''; jobs=[]
def split_row(line):
    cells=[]; buf=[]; inside=False
    for ch in line.strip().strip('|'):
        if ch=='[': inside=True
        elif ch==']': inside=False
        if ch=='|' and not inside:
            cells.append(''.join(buf).strip()); buf=[]
        else: buf.append(ch)
    cells.append(''.join(buf).strip()); return cells
for ln,line in enumerate(lines,1):
    m=re.match(r'## \d+\. (.+)',line)
    if m: section=m.group(1)
    if not line.startswith('|') or 'http' not in line: continue
    c=split_row(line)
    if len(c)!=6 or not c[0].isdigit(): continue
    lm=re.fullmatch(r'\[(.*)\]\((https?://.+)\)',c[1])
    if not lm: continue
    jobs.append(dict(master_id=len(jobs)+1,line=ln,section=section,title=lm.group(1),url=lm.group(2),company=c[2],location=c[3],posted=c[4],mode=c[5]))
assert len(jobs)==105, len(jobs)
outdir=BASE/'old105_fetches'; outdir.mkdir(exist_ok=True)
def fetch(j):
    p=outdir/f"{j['master_id']:03d}.html"
    cmd=['curl','-sS','-L','--max-time','25','--connect-timeout','10','-A','Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/136 Safari/537.36','-w','\n__META__%{http_code}\t%{url_effective}\t%{content_type}', '-o',str(p),j['url']]
    try:
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=32)
        meta=r.stdout.rsplit('__META__',1)[1].strip() if '__META__' in r.stdout else ''
        parts=meta.split('\t',2)
        status=int(parts[0]) if parts and parts[0].isdigit() else 0
        final=parts[1] if len(parts)>1 else ''
        ctype=parts[2] if len(parts)>2 else ''
        body=p.read_text('utf-8','ignore') if p.exists() else ''
        mt=re.search(r'<title[^>]*>(.*?)</title>',body,re.I|re.S)
        title=html.unescape(re.sub(r'<[^>]+>',' ',mt.group(1))).strip() if mt else ''
        return {**j,'status':status,'final':final,'content_type':ctype,'bytes':len(body),'page_title':title,'file':str(p),'error':r.stderr.strip()}
    except Exception as e: return {**j,'status':0,'final':'','content_type':'','bytes':0,'page_title':'','file':str(p),'error':repr(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex: results=list(ex.map(fetch,jobs))
out.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'jobs':len(results),'status_counts':{str(s):sum(r['status']==s for r in results) for s in sorted(set(r['status'] for r in results))},'output':str(out)},ensure_ascii=False))
