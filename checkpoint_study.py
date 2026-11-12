"""Exact checkpoint depths and bounded24-bit parents on canonical full instances."""
import argparse
from datetime import datetime,timezone
import hashlib
import inspect
import json
from pathlib import Path
import textwrap
import cupy as cp
import numpy as np
import gpu_study as original


class Packed:
    def __init__(self,data,rows,kernel):self.data,self.rows,self.kernel=data,rows,kernel
    @property
    def nbytes(self):return self.data.nbytes
    def __getitem__(self,indices):
        out=cp.empty((len(indices),2),cp.uint32)
        if len(indices):self.kernel(((2*len(indices)+255)//256,),(256,),(self.data,indices,out,np.int32(len(indices))))
        return out


class Solver(original.Solver):
    def __init__(self):
        super().__init__()
        module=cp.RawModule(code=Path('cuda/packed_links.cu').read_text(),options=('--std=c++17',))
        self.pack_kernel,self.gather_kernel=[module.get_function(name) for name in ('pack24','gather24')]
    def compact(self,links,level):
        if not self.packing:return links
        maximum=int(links.max().get()) if links.size else 0
        event=dict(level=level,rows=len(links),maximum_child_index=maximum,original_bytes=links.nbytes)
        if maximum>=1<<24:
            event.update(bits=32,stored_bytes=links.nbytes);self.packing_events.append(event);return links
        data=cp.empty(links.size*3,cp.uint8)
        if links.size:self.pack_kernel(((links.size+255)//256,),(256,),(links,data,np.int32(links.size)))
        cp.cuda.get_current_stream().synchronize()
        event.update(bits=24,stored_bytes=data.nbytes);self.packing_events.append(event)
        return Packed(data,len(links),self.gather_kernel)
    def run(self,n,k,seed,mode,regular_size=0,count=None):
        self.packing=mode.startswith('packed_');self.packing_events=[]
        self.checkpoint=int(mode[-1]) if mode[-1:].isdigit() else 0
        result=super().run(n,k,seed,'checkpoint2' if self.checkpoint else 'parents',regular_size,count)
        result.update(mode=mode,checkpoint_depth=self.checkpoint,packing_events=self.packing_events,
                      packing_scope='24-bit only after exact maximum-index check;32-bit fallback otherwise. Conversion, synchronization and release of unused allocation blocks are timed.')
        return result


# Keep the frozen solver's arithmetic/counting/reconstruction intact. The explicit
# transform changes only initial retention and the representation of stored links.
forward=textwrap.dedent(inspect.getsource(original.Solver.forward))
marker='    hashes=self.initial(n,k,seed,count);minimum=cp.arange(count,dtype=cp.uint32)'
assert forward.count(marker)==1
forward=forward.replace(marker,'    if stop==k and not explicit:retain=set(range(self.checkpoint+1,k+1))\n'+marker)
marker='        if level in retain:parents[level]=links';assert forward.count(marker)==1
forward=forward.replace(marker,'''        if level in retain:
            parents[level]=self.compact(links,level)
            del links
            if self.packing:cp.get_default_memory_pool().free_all_blocks()''')
namespace=dict(vars(original));exec(compile(forward,'<recorded-retention-transform>','exec'),namespace);Solver.forward=namespace['forward']


def main():
    assert __debug__
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--seed',type=int,default=2026111200)
    parser.add_argument('--output',default='results/checkpoint-study.json');parser.add_argument('--stochastic',action='store_true')
    parser.add_argument('--trials',type=int,default=32);args=parser.parse_args();solver=Solver()
    solver.packing=True;solver.packing_events=[]
    values=np.arange(8192,dtype=np.uint32).reshape(-1,2);values[-1]=[0xffffff,0]
    packed=solver.compact(cp.asarray(values),1);indices=np.arange(len(values)-1,-1,-1,dtype=np.uint32)
    assert isinstance(packed,Packed) and np.array_equal(cp.asnumpy(packed[cp.asarray(indices)]),values[indices])
    overflow=cp.asarray(np.array([[0x1000000,0xffffffff]],np.uint32));assert solver.compact(overflow,1) is overflow
    cases=[]
    for n,k in ((144,5),(200,9)):
        headers=range(args.seed,args.seed+args.trials) if args.stochastic else [args.seed]
        for seed in headers:
            policies=['parents','packed_parents','checkpoint1'] if args.stochastic else ['parents','checkpoint1','checkpoint2','checkpoint3','packed_parents','packed_checkpoint2']
            expected=None
            for iteration in range(1 if args.stochastic else 35):
                names=list(policies)
                if iteration%2 or (args.stochastic and seed%2):names.reverse()
                for mode in names:
                    value=solver.run(n,k,seed,mode)
                    if expected is None:expected=value['solutions']
                    else:assert value['solutions']==expected,(n,k,seed,mode)
                    if args.stochastic or iteration>=5:cases.append(dict(iteration=iteration if args.stochastic else iteration-5,**value))
            print(n,k,seed,'all policies exact',len(expected),'accepted proofs',flush=True)
            record=dict(utc=datetime.now(timezone.utc).isoformat(),seed=args.seed,stochastic=args.stochastic,
                        trials=args.trials if args.stochastic else 1,warmups=0 if args.stochastic else 5,samples=1 if args.stochastic else 30,
                        packing_validation_values=values.size,overflow_fallback_checked=True,cases=cases,
                        forward_source_sha256=hashlib.sha256(forward.encode()).hexdigest(),
                        cubin_sha256=hashlib.sha256(Path("build/wagner.cubin").read_bytes()).hexdigest(),
                        source_sha256={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in
                            ('checkpoint_study.py','gpu_study.py','cuda/packed_links.cu','cuda/wagner.cu','experiments/birthday.py','native/tromp_bridge.cpp')},
                        scope='Canonical exact same leaves and pair emission; adjustable discarded early parent depths,24-bit stored links only when every child fits. No bucket truncation added. Conversion/unpack/cache-release and all independent/native verification included. Fixed-input latency and disjoint stochastic nonces are separate records; no-hit headers retained.')
            Path(args.output).write_text(json.dumps(record,indent=2)+'\n')


if __name__=='__main__':main()
