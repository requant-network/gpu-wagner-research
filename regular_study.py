"""Matched-leaf single-list/regular-list comparisons with complete CPU solution sets."""
import argparse,hashlib,json,pathlib,time
from datetime import datetime,timezone
from gpu_study import Solver
from experiments.birthday import leaves,solve

assert __debug__
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--seed',type=int,default=20261109)
parser.add_argument('--output',default='results/regular-study.json');args=parser.parse_args();solver=Solver();cases=[]
for n,k,count,size in ((24,2,1024,256),(32,3,512,64),(48,3,8192,1024)):
    values=leaves(n,k,args.seed,count)
    for regular in (0,size):
        started=time.perf_counter();reference,counts=solve(values,n,k,regular);cpu_wall=(time.perf_counter()-started)*1000
        expected=[list(x) for x in reference];samples=[];result=None
        for iteration in range(35):
            result=solver.run(n,k,args.seed,'parents',regular,count)
            assert result['solutions']==expected
            if iteration>=5:samples.append(result['complete_verified_wall_ms'])
        cases.append(dict(n=n,k=k,seed=args.seed,initial_items=count,regular_list_size=regular,
            cpu_reference_wall_ms=cpu_wall,cpu_round_sizes=counts,cpu_and_gpu_solution_sets_equal=True,
            solutions=expected,rounds=result['rounds'],observed_pool_reserved_bytes=result['observed_pool_reserved_bytes'],
            samples_ms=samples))
        print(n,k,count,regular,len(expected),flush=True)
sources=['regular_study.py','gpu_study.py','experiments/birthday.py','cuda/wagner.cu','native/tromp_bridge.cpp']
record=dict(status='completed',utc=datetime.now(timezone.utc).isoformat(),seed=args.seed,warmups=5,samples=30,cases=cases,
    source_sha256={p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in sources},
    scope='Same hash values and initial leaf count within each single/regular pair; regular mode additionally requires one leaf per origin list. Complete CPU solution sets compared, no bucket caps. GPU full verified wall uses parent pointers and five warmups/thirty observations. CPU oracle is one exhaustive reference call, not an optimized throughput baseline. These are scaled mathematical GBP models, not a deployed Requihash miner.')
pathlib.Path(args.output).write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
