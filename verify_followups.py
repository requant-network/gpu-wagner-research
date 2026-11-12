"""CPU replay of follow-up evidence, provenance and derived timing summaries."""
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import median
assert __debug__
PATTERNS = ('canonical-*.json','checkpoint-*.json')
paths=sorted(set(p for pattern in PATTERNS for p in Path('results').glob(pattern)))
assert len(paths)==7,(len(paths),[p.name for p in paths])
records={p.name:json.loads(p.read_text()) for p in paths}
def binding(name,expected,result=False):
 p=(Path('results')/name) if result else Path(name)
 assert not Path(name).is_absolute() and ':' not in name and '..' not in Path(name).parts
 assert hashlib.sha256(p.read_bytes()).hexdigest()==expected,(p,expected)
def provenance(r):
 if isinstance(r,dict):
  for key,v in r.items():
   if key in ('source_sha256','artifacts_sha256','public_artifacts_sha256','result_sha256'):
    for name,expected in v.items():binding(name,expected,key=='result_sha256')
   elif isinstance(v,(dict,list)):provenance(v)
 elif isinstance(r,list):
  for v in r:provenance(v)
for r in records.values():provenance(r)
from canonical_cpu_study import LeafOracle
from experiments.birthday import verify
checked=set()
for name,r in records.items():
 if name.startswith('canonical-cpu'):assert len(r['cases'])==32
 if name.startswith('checkpoint-'):
  assert r['packing_validation_values']==8192 and r['overflow_fallback_checked']
  assert len(r['cases'])==(192 if r['stochastic'] else 360)
 for c in r.get('cases',[]):
  if c.get('exit_code',0):continue
  v=c.get('result',c)
  if 'solutions' not in v:continue
  for proof in v['solutions']:
   key=(c['n'],c['k'],c['seed'],tuple(proof))
   if key not in checked:
    assert verify(LeafOracle(c['n'],c['k'],c['seed'],1<<(c['n']//(c['k']+1)+1)),c['n'],c['k'],proof)
    checked.add(key)

rows=[]
def timings(value,labels,route=''):
 if isinstance(value,list):
  assert len(value)==30 and all(isinstance(v,(int,float)) and math.isfinite(v) and v>=0 for v in value),(labels,route)
  rows.append(dict(**labels,variant_scope=route,median_ms=median(value),p95_ms=sorted(value)[28],repetitions=len(value)))
 elif isinstance(value,dict):
  for key,v in value.items():timings(v,labels,(route+'/' if route else '')+key)
for name,r in records.items():
 for index,c in enumerate(r.get('cases',[])):
  labels=dict(file=name,case=index,seed=c.get('seed',r.get('seed','')),**{key:c.get(key,'') for key in ('application','n','m','k','p','columns','steps','payload_bytes','batch','variant','pattern')})
  v=c.get('result',c)
  for key in ('samples','samples_ms','resident_graph_device_ms'):
   if isinstance(v.get(key),(dict,list)):timings(v[key],labels,key)
from collections import defaultdict
for name,r in records.items():
 groups=defaultdict(list)
 for c in r.get('cases',[]):groups[(c['n'],c['k'],c.get('mode','cpu-'+str(c.get('threads',''))))].append(c)
 for (n,k,mode),cases in groups.items():
  good=[c for c in cases if c.get('exit_code',0)==0]
  values=[c['result']['solve_reconstruction_ms'] if 'result' in c else c['solve_wall_ms'] for c in good]
  complete=[c.get('process_wall_ms',c.get('complete_verified_wall_ms')) for c in good]
  proofs=[len(c.get('result',c)['solutions']) for c in good]
  rows.append(dict(file=name,n=n,k=k,mode=mode,observations=len(cases),successfully_completed=len(good),
                   latency_scope='CPU fresh process; independent Python proof replay excluded' if mode.startswith('cpu-') else 'GPU complete solve plus independent/native verification',
                   solve_median_ms=median(values) if values else '',boundary_median_ms=median(complete) if complete else '',
                   boundary_p95_ms=sorted(complete)[math.ceil(.95*len(complete))-1] if complete else '',
                   returned_proofs=sum(proofs),zero_yield_observations=proofs.count(0),
                   maximum_observed_gpu_pool_bytes=max((c.get('observed_pool_reserved_bytes',0) for c in good),default=0),
                   maximum_cpu_process_rss_kib=max((c.get('result',{}).get('peak_rss_kib',0) for c in good),default=0)))
if rows:
 with Path('results/followup-summary.csv').open('w',newline='') as out:
  writer=csv.DictWriter(out,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
print(len(records),'follow-up records validated;',len(rows),'median/p95 timing rows')
