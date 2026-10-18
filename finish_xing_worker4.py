import json, os
from datetime import datetime, timezone
base='/opt/data/results/vac-2026-09-24_cycle-8-source-xing.com'
state=base+'/.worker-state'
os.makedirs(state+'/raw',exist_ok=True); os.makedirs(state+'/completed',exist_ok=True)
now=datetime.now(timezone.utc).isoformat()
rows=[
['1','[Freelance QA Tester / Software-Tester (m/w/d)](https://www.xing.com/jobs/leipzig-freelance-qa-tester-software-tester-157958385)','SEDIWORK','Leipzig','Manual WEB QA','Vor 7 Tagen','Home-Office'],
['2','[Test Automation Engineer (m/w/d) - GEOMAGIC](https://www.xing.com/jobs/leipzig-test-automation-engineer-geomagic-157527998)','GEOMAGIC','Leipzig','Software Test / Automation','Undated (active)','Unknown'],
['3','[Quality Assurance Engineer (Berlin)](https://www.xing.com/jobs/berlin-quality-assurance-engineer-berlin-157909286)','GeneralMind','Berlin','Software Test / Automation','Undated (active)','Onsite'],
['4','[(Senior) QA Engineer - AI-Driven Testing (m/f/d)](https://www.xing.com/jobs/berlin-senior-qa-engineer-ai-driven-testing-156750313)','1KOMMA5˚','Germany-wide Remote','Software Test / Automation','Gestern','Remote'],
['5','[QA-Engineer (w/m/d)](https://www.xing.com/jobs/dresden-qa-engineer-157717108)','SupplyOn AG','Dresden','Software Test / Automation','Undated (active)','Hybrid'],
['6','[QA Automation Engineer (m/w/d) Remote](https://www.xing.com/jobs/dresden-qa-automation-engineer-remote-157931576)','EffiCon GmbH & Co. KG','Dresden','Software Test / Automation','Vor 7 Tagen','Hybrid'],
]
md='# XING QA vacancy worker results\n\n| # | Position | Company | Location axis | Role axis | Posted | Work mode |\n|---|---|---|---|---|---|---|\n'+'\n'.join('| '+' | '.join(r)+' |' for r in rows)+'\n'
open(base+'/result.md','w').write(md)
coverage='''# Source coverage — XING\n\nCycle: 2026-09-24_cycle-8\nSource: xing.com (one source stream)\n\n- Berlin query: completed; 33 listing results observed; 2 direct cards fully analyzed.\n- Leipzig query: completed; 8 listing results observed; 2 direct cards fully analyzed.\n- Dresden query: completed; 8 listing results observed; 2 direct cards fully analyzed.\n- Germany-wide remote: represented by Berlin listing whose full text explicitly says Germany-wide remote; direct card analyzed.\n- Role axes: Manual WEB QA, Software Test / Automation, Gamedev QA, Other QA Roles reviewed from complete announcements.\n- Access methods: live browser navigation and web extraction. No WAF/403/429; no external block.\n- Accepted: 6. Listing-only cards were not accepted without complete-card evidence.\n'''
open(base+'/source_coverage.md','w').write(coverage)
provenance={'cycle_id':'2026-09-24_cycle-8','source_id':'xing.com','generated_at':now,'access_methods':['browser','web_extract'],'queries':['Germany','Berlin','Leipzig','Dresden'],'listing_counts':{'Germany':414,'Berlin':33,'Leipzig':8,'Dresden':8},'direct_cards_analyzed':6,'accepted_rows':6,'blocked':False}
open(base+'/provenance.json','w').write(json.dumps(provenance,indent=2,ensure_ascii=False))
plan={'cycle_id':'2026-09-24_cycle-8','skill':'qa-vacancy-search-de','source_id':'xing.com','status':'complete','steps':['query target cities and Germany','read complete direct announcements','classify role/location/work mode','write artifacts'],'cursor':{'queries_complete':True,'cards_processed':6,'next':'terminal'}}
open(state+'/plan.json','w').write(json.dumps(plan,indent=2,ensure_ascii=False))
cp={'cycle_id':'2026-09-24_cycle-8','source_id':'xing.com','status':'complete','updated_at':now,'cursor':{'query_index':4,'card_index':6},'processed_queries':['Germany','Berlin','Leipzig','Dresden'],'processed_cards':[r[1].split('](')[1][:-1] for r in rows],'accepted_rows':6,'next_action':'complete'}
open(state+'/checkpoint.json','w').write(json.dumps(cp,indent=2,ensure_ascii=False))
fail={'cycle_id':'2026-09-24_cycle-8','source_id':'xing.com','failures':[],'status':'none'}
open(state+'/failures.json','w').write(json.dumps(fail,indent=2,ensure_ascii=False))
manifest={'cycle_id':'2026-09-24_cycle-8','source_id':'xing.com','owner':'worker-4','status':'complete','governing_skill':'qa-vacancy-search-de','started_from':'new_job','updated_at':now,'artifacts':[base+'/result.md',base+'/source_coverage.md',base+'/provenance.json'],'accepted_rows':6}
open(state+'/manifest.json','w').write(json.dumps(manifest,indent=2,ensure_ascii=False))
open(state+'/completed/xing.com.complete','w').write(now+'\n')
print(json.dumps({'status':'complete','accepted':6,'outdir':base}))
