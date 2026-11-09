"""Check whether allocator retention explains checkpoint recomputation memory cost."""
import argparse,hashlib,json,pathlib
from datetime import datetime,timezone
import cupy as cp
from gpu_study import Solver

class CompactSolver(Solver):
    def forward(self,n,k,seed,count,stop,retain,explicit=False,regular_size=0):
        if stop<k:cp.get_default_memory_pool().free_all_blocks()
        return super().forward(n,k,seed,count,stop,retain,explicit,regular_size)

assert __debug__
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--seed',type=int,default=20261109)
parser.add_argument('--output',default='results/allocator-study.json');args=parser.parse_args()
ordinary,compact=Solver(),CompactSolver();cases=[]
for n,k in ((144,5),(200,9)):
    samples={name:{scope:[] for scope in ('complete_verified_wall_ms','observed_pool_reserved_bytes')} for name in ('parents','checkpoint2','checkpoint2_release')};expected=None
    for iteration in range(35):
        names=list(samples)
        if iteration%2:names.reverse()
        for name in names:
            solver=compact if name=='checkpoint2_release' else ordinary
            result=solver.run(n,k,args.seed,'checkpoint2' if name.startswith('checkpoint2') else 'parents')
            if expected is None:expected=result['solutions']
            else:assert expected==result['solutions']
            if iteration>=5:
                for scope in samples[name]:samples[name][scope].append(result[scope])
    cases.append(dict(n=n,k=k,seed=args.seed,solutions=expected,all_policies_exact=True,samples=samples))
    print(n,k,'allocator follow-up completed',flush=True)
sources=['allocator_study.py','gpu_study.py','experiments/birthday.py','cuda/wagner.cu','native/tromp_bridge.cpp']
record=dict(status='completed',utc=datetime.now(timezone.utc).isoformat(),seed=args.seed,warmups=5,samples=30,cases=cases,
    source_sha256={p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in sources},
    scope='Same solver and accepted proof sets. Follow-up releases unused CuPy pool blocks before each early-level reconstruction; kept parent arrays remain alive. Release cost is inside the full verified timer. Allocation caching is an implementation variable, not a theoretical time-memory bound. Five warm-ups/thirty paired alternating repetitions, both standard parameter sets.')
pathlib.Path(args.output).write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
