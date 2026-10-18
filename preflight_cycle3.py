import urllib.request, urllib.parse, json, time, re, html
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131 Safari/537.36'
def fetch(name,url,headers=None,counters=None):
 h={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8','Accept-Language':'de-DE,de;q=0.9,en;q=0.5'}
 if headers:h.update(headers)
 req=urllib.request.Request(url,headers=h)
 t=time.monotonic()
 try:
  with urllib.request.urlopen(req,timeout=45) as r: b=r.read(); st=r.status; final=r.geturl(); ra=r.headers.get('Retry-After')
 except urllib.error.HTTPError as e: b=e.read();st=e.code;final=e.geturl();ra=e.headers.get('Retry-After')
 except Exception as e:return dict(source=name,url=url,status='NETWORK_ERROR',latency_ms=round((time.monotonic()-t)*1000),count=0,error=repr(e))
 s=b.decode('utf-8','replace')
 n=0
 if counters:
  for pat,mode in counters:
   if mode=='json':
    try:
     d=json.loads(s); x=d
     for key in pat.split('.'):
      if isinstance(x,dict):x=x.get(key,[])
      else:break
     n=len(x) if isinstance(x,list) else 0
    except:pass
   else:n+=len(re.findall(pat,s,re.I|re.S))
 else:n=len(re.findall(r'href=["\'][^"\']+',s,re.I))
 return dict(source=name,url=url,status=st,latency_ms=round((time.monotonic()-t)*1000),count=n,bytes=len(b),final=final,retry_after=ra,body=s[:300].replace('\n',' '))
R=[]
# sequential, one request per host
li='https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?'+urllib.parse.urlencode({'keywords':'Softwaretester QA Engineer Testautomatisierung','location':'Deutschland','f_TPR':'r2592000','f_WT':'2'})
R.append(fetch('LinkedIn Jobs',li,counters=[(r'<li>.*?</li>','html')]))
aa='https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs?'+urllib.parse.urlencode({'was':'Softwaretester Testautomatisierung Qualitätssicherung','wo':'Deutschland','size':50,'page':1})
R.append(fetch('Arbeitsagentur Jobsuche',aa,{'X-API-Key':'jobboerse-jobsuche-service','Accept':'application/json'},[(r'stellenangebote','json')]))
R.append(fetch('StepStone','https://www.stepstone.de/jobs/softwaretester-in-berlin.html',counters=[(r'<article\b','html'),(r'data-jobid=','html')]))
R.append(fetch('XING Jobs','https://www.xing.com/jobs/search?keywords=Softwaretester%20Testengineer&location=Deutschland&date_range=last_month',counters=[(r'/jobs/[^"?#]+-\d+','html')]))
R.append(fetch('Hitmarker','https://hitmarker.net/jobs?search=Game+QA+Germany',counters=[(r'href=["\']/jobs/[^"\']+','html')]))
# deterministic public employer ATS endpoint with German query; direct ATS cards
R.append(fetch('Direct company ATS and career sites','https://careers.asp.net/en/search-results?keywords=Software%20Quality%20Assurance%20Germany',counters=[(r'job-search__results|search-result','html')]))
R.append(fetch('Remotive','https://remotive.com/api/remote-jobs?'+urllib.parse.urlencode({'search':'QA Engineer Software Test Germany','limit':100}),headers={'Accept':'application/json'},counters=[(r'jobs','json')]))
R.append(fetch('Arbeitnow Job Board API','https://www.arbeitnow.com/api/job-board-api',{'Accept':'application/json'},[(r'data','json')]))
open('/opt/data/qa-vacancy-project/preflight_cycle3_raw.json','w').write(json.dumps(R,ensure_ascii=False,indent=2))
for x in R:x.pop('body',None)
print(json.dumps(R,ensure_ascii=False,indent=2))
