import sys,json
sys.path.insert(0,'/opt/data/qa-vacancy-project')
from preflight_cycle3 import fetch
R=[]
R.append(fetch('Arbeitsagentur fallback','https://www.arbeitsagentur.de/jobsuche/suche?was=Softwaretester%20Testautomatisierung&wo=Deutschland',counters=[(r'jobdetail/|jobs-guest|result-list-item','html')]))
R.append(fetch('StepStone fallback','https://www.stepstone.de/jobs/qa-test/in-berlin.html',counters=[(r'data-jobid=|stellenangebote--','html')]))
R.append(fetch('Hitmarker fallback','https://hitmarker.net/jobs',counters=[(r'/jobs/[^"?#]+','html')]))
R.append(fetch('Company ATS fallback','https://jobs.sap.com/search/?q=Software%20Quality%20Assurance&location=Germany',counters=[(r'/job/|search-result|card','html')]))
open('/opt/data/qa-vacancy-project/preflight_cycle3_fallback_raw.json','w').write(json.dumps(R,ensure_ascii=False,indent=2))
for x in R:x.pop('body',None)
print(json.dumps(R,ensure_ascii=False,indent=2))
