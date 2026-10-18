import json, re, time, urllib.parse, urllib.request, html, os
from datetime import datetime, timezone
OUT='/opt/data/results/vac-2026-09-24-source-01-cycle-2'
os.makedirs(OUT,exist_ok=True)
roles=['Manual WEB QA','Software Test / Automation','Gamedev QA','Other QA Roles']
locs=['Berlin','Leipzig','Dresden','Germany-wide Remote']
role_q={'Manual WEB QA':'Softwaretester QA Engineer','Software Test / Automation':'Software Test Automation Engineer','Gamedev QA':'Game QA Tester','Other QA Roles':'Quality Assurance Test Engineer'}
loc_q={'Berlin':'Berlin Germany','Leipzig':'Leipzig Germany','Dresden':'Dresden Germany','Germany-wide Remote':'Germany remote'}
UA={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36','Accept-Language':'de-DE,de;q=0.9,en;q=0.8'}
def get(u,headers=UA):
 req=urllib.request.Request(u,headers=headers); r=urllib.request.urlopen(req,timeout=30); return r.status,r.geturl(),r.read().decode('utf-8','replace')
def clean(s): return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',s or ''))).strip()
def classify(j,loc):
 t=(j.get('title') or '').lower(); d=(j.get('description') or '').lower(); blob=t+' '+d
 cat='Gamedev QA' if re.search(r'game|gaming|spiel',blob) else ('Software Test / Automation' if re.search(r'automatis|test engineer|software test|testautomatis',blob) else ('Manual WEB QA' if re.search(r'manual|web|qa engineer|softwaretest',blob) else 'Other QA Roles'))
 eligible=False
 if loc=='Germany-wide Remote': eligible=bool(re.search(r'\b(remote|home office|homeoffice)\b',blob))
 else: eligible=loc.lower() in blob
 return cat,eligible
allc=[]; coverage=[]; failures=[]
# LinkedIn guest API all 16
for loc in locs:
 for cat in roles:
  q=role_q[cat]; lq=loc_q[loc]
  params={'keywords':q,'location':lq,'f_TPR':'r2592000','f_JT':'F'}
  if loc=='Germany-wide Remote': params['f_WT']='2'
  u='https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?'+urllib.parse.urlencode(params)
  try:
   st,final,body=get(u); open(f'{OUT}/linkedin_{loc}_{cat.replace("/","_").replace(" ","_")}.html','w').write(body)
   cards=re.findall(r'<li>(.*?)</li>',body,re.S)
   n=0
   for card in cards:
    m=re.search(r'<a[^>]+href="([^"]+)"',card)
    if not m: continue
    url=html.unescape(m.group(1)).split('?')[0]; tid=re.search(r'-(\d+)$',url)
    if not tid: continue
    # direct job API full capture
    ju=f'https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{tid.group(1)}'
    try:
     js,jf,jb=get(ju); desc=clean(re.search(r'<div class="show-more-less-html__markup[^>]*>(.*?)</div>',jb,re.S).group(1) if re.search(r'<div class="show-more-less-html__markup[^>]*>(.*?)</div>',jb,re.S) else '')
     title=clean(re.search(r'<h2[^>]*>(.*?)</h2>',jb,re.S).group(1)) if re.search(r'<h2[^>]*>(.*?)</h2>',jb,re.S) else ''
     company=clean(re.search(r'<h4[^>]*>(.*?)</h4>',jb,re.S).group(1)) if re.search(r'<h4[^>]*>(.*?)</h4>',jb,re.S) else ''
     j={'source':'LinkedIn Jobs','url':url,'title':title,'company':company,'description':desc,'location_query':loc,'role_query':cat,'status':js,'raw':jb}
     c,e=classify(j,loc); j['location_axis']=loc if e else None;j['role_axis']=c;j['eligible_by_query']=e;allc.append(j);n+=1
    except Exception as x: failures.append(f'LinkedIn direct {url}: {x}')
   coverage.append({'source':'LinkedIn Jobs','location':loc,'role':cat,'query':u,'status':st,'cards':n,'capture':os.path.basename(u.split('?')[0].split('/')[-1])})
  except Exception as e: failures.append(f'LinkedIn {loc}/{cat}: {e}');coverage.append({'source':'LinkedIn Jobs','location':loc,'role':cat,'query':u,'status':'FAILED','error':str(e)})
# Remotive API per axes; API + direct card retrieval are two methods
rbase='https://remotive.com/api/remote-jobs'
for loc in locs:
 for cat in roles:
  params={'search':role_q[cat],'limit':'100'}
  u=rbase+'?'+urllib.parse.urlencode(params)
  try:
   st,final,body=get(u,{'User-Agent':'curl/8.5.0','Accept':'application/json'}); data=json.loads(body)
   open(f'{OUT}/remotive_{loc}_{cat.replace("/","_").replace(" ","_")}.json','w').write(body)
   n=0
   for j in data.get('jobs',[]):
    x={'source':'Remotive','url':j.get('url'),'title':j.get('title'),'company':j.get('company_name'),'description':j.get('description'),'location_query':loc,'role_query':cat,'published_at':j.get('publication_date'),'candidate_location':j.get('candidate_required_location'),'raw':j}
    c,e=classify(x,loc); x['role_axis']=c;x['eligible_by_query']=e
    # direct card second method
    try:
     ds,df,db=get(j['url']);x['direct_status']=ds;x['direct_url']=df;x['direct_html']=db;n+=1;allc.append(x)
    except Exception as z: failures.append(f'Remotive direct {j.get("url")}: {z}')
   coverage.append({'source':'Remotive','location':loc,'role':cat,'query':u,'status':st,'cards_verified':n})
  except Exception as e: failures.append(f'Remotive {loc}/{cat}: {e}');coverage.append({'source':'Remotive','location':loc,'role':cat,'query':u,'status':'FAILED','error':str(e)})
# dedupe direct URLs, keep only affirmative matches
uniq={}
for x in allc:
 if not x.get('eligible_by_query') or not x.get('url'): continue
 uniq.setdefault(x['url'].split('?')[0],x)
json.dump(list(uniq.values()),open(f'{OUT}/candidates.json','w'),ensure_ascii=False,indent=2)
json.dump(coverage,open(f'{OUT}/coverage.json','w'),ensure_ascii=False,indent=2)
json.dump(failures,open(f'{OUT}/failures.json','w'),ensure_ascii=False,indent=2)
# raw full announcements
for i,x in enumerate(uniq.values(),1):
 with open(f'{OUT}/candidate_{i:03d}_full.md','w') as f:
  f.write(f"# {x.get('title')}\n\n- Source: {x['source']}\n- URL: {x['url']}\n- Company: {x.get('company')}\n- Query: {x.get('location_query')} / {x.get('role_query')}\n- Full announcement:\n\n")
  f.write((x.get('description') or x.get('raw') or '').replace('\r',''))
  f.write('\n')
print('unique eligible',len(uniq),'failures',len(failures))
