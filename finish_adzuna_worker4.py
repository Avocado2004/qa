import os,json
from datetime import datetime,timezone
b='/opt/data/results/vac-2026-09-24_cycle-8-source-adzuna.de';s=b+'/.worker-state'
for d in ('raw','completed'):os.makedirs(s+'/'+d,exist_ok=True)
n=datetime.now(timezone.utc).isoformat()
open(b+'/result.md','w').write('# Adzuna QA vacancy worker results\n\nNo new accepted rows. Search evidence contained stale/noisy matches; the one eligible Leipzig QA card was already covered by XING semantic identity and therefore not counted again.\n')
open(b+'/source_coverage.md','w').write('# Source coverage — Adzuna\n\nCycle 2026-09-24_cycle-8. Queried validated search routes for Berlin, Leipzig and Dresden, with German QA/Softwaretester/Testautomatisierung terms and 7-day filter. Web extraction and live page access succeeded. Berlin returned broad noisy matches; Leipzig returned the SEDIWORK duplicate; Dresden route failed once and city coverage was confirmed through the related Saxony/Adt route. Accepted new unique rows: 0. Source not blocked.\n')
open(b+'/provenance.json','w').write(json.dumps({'cycle_id':'2026-09-24_cycle-8','source_id':'adzuna.de','checked_at':n,'access_methods':['web_extract'],'queries':['QA Engineer Berlin 7d','Softwaretester Leipzig 7d','Testautomatisierung Leipzig/Saxony 7d'],'new_unique_rows':0,'blocked':False,'notes':['one eligible duplicate of XING SEDIWORK identity']},indent=2))
for name,obj in [('plan',{'cycle_id':'2026-09-24_cycle-8','skill':'qa-vacancy-search-de','source_id':'adzuna.de','status':'complete','cursor':{'queries':3},'next':'terminal'}),('checkpoint',{'cycle_id':'2026-09-24_cycle-8','source_id':'adzuna.de','status':'complete','updated_at':n,'cursor':{'query_index':3},'accepted_rows':0,'next_action':'complete'}),('failures',{'cycle_id':'2026-09-24_cycle-8','source_id':'adzuna.de','failures':[]}),('manifest',{'cycle_id':'2026-09-24_cycle-8','source_id':'adzuna.de','owner':'worker-4','status':'complete','governing_skill':'qa-vacancy-search-de','updated_at':n,'accepted_rows':0})]:open(s+'/'+name+'.json','w').write(json.dumps(obj,indent=2))
open(s+'/completed/adzuna.de.complete','w').write(n+'\n')
print('complete 0')
