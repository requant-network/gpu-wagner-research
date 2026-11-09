"""Fixed-input five-warm-up/thirty-sample canonical solver comparisons."""
import argparse,hashlib,json,pathlib
from datetime import datetime,timezone
from gpu_study import Solver

assert __debug__
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--seed',type=int,default=20261109)
parser.add_argument('--output',default='results/latency-study.json');args=parser.parse_args();solver=Solver();cases=[]
for n,k in ((96,5),(144,5),(200,9)):
    expected=None;samples={mode:{scope:[] for scope in ('solve_wall_ms','verify_wall_ms','complete_verified_wall_ms')} for mode in ('vectors','parents','checkpoint2')};memory={}
    for iteration in range(35):
        modes=list(samples)
        if iteration%2:modes.reverse()
        for mode in modes:
            result=solver.run(n,k,args.seed,mode)
            if expected is None:expected=result['solutions']
            else:assert result['solutions']==expected
            memory[mode]=max(memory.get(mode,0),result['observed_pool_reserved_bytes'])
            if iteration>=5:
                for scope in samples[mode]:samples[mode][scope].append(result[scope])
    cases.append(dict(n=n,k=k,seed=args.seed,solutions=expected,all_memory_policies_exact=True,samples=samples,observed_pool_reserved_bytes=memory))
    print(n,k,'latency comparison completed',flush=True)
sources=['latency_study.py','gpu_study.py','experiments/birthday.py','cuda/wagner.cu','native/tromp_bridge.cpp']
record=dict(status='completed',utc=datetime.now(timezone.utc).isoformat(),seed=args.seed,warmups=5,samples=30,cases=cases,
    source_sha256={p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in sources},
    scope='Same canonical input and accepted proof set, five warm-ups/thirty samples, alternating policy order. solve_wall includes hashing, new work-buffer allocations, sorting, reconstruction and D2H. Complete verified wall additionally includes independent exact verification and native standard-parameter verification. Garbage collection/cache release precedes each timed call; no clock or power changes.')
pathlib.Path(args.output).write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
