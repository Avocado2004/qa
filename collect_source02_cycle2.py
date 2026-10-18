import os,json,time,urllib.request,urllib.parse,datetime
OUT='/opt/data/results/vac-2026-09-24-source-02-cycle-2'
RAW=OUT+'/raw'; os.makedirs(RAW,exist_ok=True)
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131 Safari/537.36'
def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json,text/html','X-API-Key':'jobboerse-jobsuche-service'})
 with urllib.request.urlopen(req,timeout=45) as r: return r.status,r.geturl(),r.read()
# 4 role categories
cats={
'manual_web_qa':['Manuelle Tests','Manual QA','Web QA'],
'software_test_engineer':['Softwaretester','Test Engineer','Testautomatisierer','Qualitätssicherung'],
'gamedev_qa_engineer':['Game QA','Game Tester','QA Gamedev','Spiele Tester'],
'other_qa_roles':['QA Engineer','Quality Assurance','Test Automation','QA Automatisierung']}
# 4 location/work-mode modes
modes={'berlin':'Berlin','leipzig':'Leipzig','dresden':'Dresden','germany_remote':'Deutschland remote'}
AA='https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs'
K='jobboerse-jobsuche-service'
summary=[]
# AA all query x modes, paginate max observed
for cat,terms in cats.items():
 for mode,loc in modes.items():
  for term in terms:
   q=urllib.parse.urlencode({'was':term,'wo':loc,'size':50,'page':1})
   page=1; rows=[]; maxpages=1
   while page<=10:
    u=AA+'?'+q.replace('page=1',f'page={page}')
    try: st,final,b=get(u)
    except Exception as e:
     summary.append({'source':'arbeitsagentur','category':cat,'mode':mode,'term':term,'page':page,'error':str(e)}); break
    open(f'{RAW}/arbeitsagentur__{cat}__{mode}__{term.replace(" ","_")}__p{page}.json','wb').write(b)
    try:d=json.loads(b)
    except Exception as e: summary.append({'source':'arbeitsagentur','category':cat,'mode':mode,'term':term,'page':page,'error':f'json {e} {b[:200]}'}); break
    got=d.get('stellenangebote',[]); rows+=got
    meta=d.get('meta',{}); maxpages=meta.get('maxErgebnisseSeiten',1)
    if page>=maxpages: break
    page+=1; time.sleep(.35)
   summary.append({'source':'arbeitsagentur','category':cat,'mode':mode,'term':term,'records':len(rows),'pages':page,'max_pages':maxpages})
# Arbeitnow all pages, local full announcement discovery
u='https://www.arbeitnow.com/api/job-board-api'; allrows=[]
for page in range(1,80):
 try: st,final,b=get(u+('' if page==1 else f'?page={page}'))
 except Exception as e: summary.append({'source':'arbeitnow','page':page,'error':str(e)}); break
 open(f'{RAW}/arbeitnow_page_{page:02}.json','wb').write(b)
 try:d=json.loads(b)
 except Exception as e: summary.append({'source':'arbeitnow','page':page,'error':f'json {e} {b[:200]}'}); break
 got=d.get('data',[]); allrows+=got
 nxt=d.get('links',{}).get('next')
 if not got or not nxt: summary.append({'source':'arbeitnow','terminal_page':page,'records_page':len(got)}); break
 time.sleep(.3)
# local matrix hits using whole description semantic discovery terms
qa_terms=['qa','quality assurance','test engineer','softwaretest','testautomation','test automation','qualitätssicherung','game tester','game qa','spiele test','tester','testing engineer']
loc_terms={'berlin':['berlin'],'leipzig':['leipzig'],'dresden':['dresden'],'germany_remote':['germany remote','remote germany','deutschland remote','remote deutschland','germany-wide remote','100% remote germany']}
for r in allrows:
 text=' '.join(str(r.get(k,'')) for k in ['title','description','tags','location']).lower()
 if not any(t in text for t in qa_terms): continue
 for cat in cats:
  ct=('manual' if any(x in text for x in ['manual','manuelle']) else 'gamedev' if any(x in text for x in ['game','spiel']) else 'other')
  if (cat=='manual_web_qa' and ct!='manual') or (cat=='gamedev_qa_engineer' and ct!='gamedev') or (cat in ['software_test_engineer','other_qa_roles'] and ct!='other'): continue
  for mode,terms in loc_terms.items():
   if any(x in text for x in terms): summary.append({'source':'arbeitnow','category':cat,'mode':mode,'id':r.get('id'),'title':r.get('title'),'company':r.get('company_name'),'location':r.get('location'),'url':r.get('url')})
json.dump(summary,open(OUT+'/collection_summary.json','w'),ensure_ascii=False,indent=2)
json.dump(allrows,open(RAW+'/arbeitnow_all_records.json','w'),ensure_ascii=False,indent=2)
print(json.dumps({'summary':len(summary),'arbeitnow_records':len(allrows),'hits':sum(1 for x in summary if x.get('id')),'errors':[x for x in summary if x.get('error')]},ensure_ascii=False,indent=2))
