"""Complete canonical GPU Wagner solver with exact memory-policy comparisons."""
import argparse,ctypes,gc,hashlib,json,pathlib,struct,time
from datetime import datetime,timezone
import cupy as cp
import numpy as np
from experiments.birthday import canonical,header,leaves,solve,verify

class LeafOracle:
    def __init__(self,n,k,seed,count):self.n=n;self.k=k;self.seed=seed;self.count=count;self.cache={}
    def __len__(self):return self.count
    def __getitem__(self,index):
        per=512//self.n;group=index//per;size=self.n//8
        if group not in self.cache:self.cache[group]=hashlib.blake2b(header(self.seed)+struct.pack('<I',group),digest_size=per*size,person=b'ZcashPoW'+struct.pack('<II',self.n,self.k)).digest()
        start=index%per*size;return int.from_bytes(self.cache[group][start:start+size],'big')

class Solver:
    def __init__(self):
        module=cp.RawModule(path=str(pathlib.Path('build/wagner.cubin').resolve()))
        self.kernels={name:module.get_function(name) for name in ('initialize_midstate','hash_leaves','make_keys','pair_counts','emit_pairs')}
        self.dummy=cp.empty(1,cp.uint32)
    def initial(self,n,k,seed,count):
        mid=cp.empty(8,cp.uint64);hashes=cp.empty((count,k+1),cp.uint32)
        self.kernels['initialize_midstate']((1,),(1,),(mid,np.uint32(seed),np.int32(n),np.int32(k)))
        groups=(count+512//n-1)//(512//n)
        self.kernels['hash_leaves'](((groups+127)//128,),(128,),(mid,hashes,np.int32(count),np.int32(n),np.int32(k)))
        return hashes
    def forward(self,n,k,seed,count,stop,retain,explicit=False,regular_size=0):
        hashes=self.initial(n,k,seed,count);minimum=cp.arange(count,dtype=cp.uint32)
        tags=(cp.arange(count,dtype=cp.int32)//regular_size) if regular_size else cp.zeros(count,cp.int32)
        vectors=minimum.reshape(-1,1) if explicit else self.dummy;parents={};rounds=[];reserved=0;min_free=1<<64
        bits=n//(k+1);width=1
        for level in range(1,stop+1):
            digits=hashes.shape[1];count=len(hashes);final=level==k
            if not count:break
            keys=cp.empty(count,cp.uint64)
            self.kernels['make_keys'](((count+255)//256,),(256,),(hashes,tags,keys,*[np.int32(x) for x in (count,digits,bits,final,bool(regular_size))]))
            order=cp.argsort(keys,kind='stable').astype(cp.uint32);sorted_keys=keys[order];counts=cp.empty(count,cp.uint32)
            self.kernels['pair_counts'](((count+255)//256,),(256,),(sorted_keys,order,minimum,tags,counts,np.int32(count),np.int32(bool(regular_size))))
            offsets=cp.empty(count+1,cp.uint64);offsets[0]=0;cp.cumsum(counts,dtype=cp.uint64,out=offsets[1:]);total=int(offsets[-1].get())
            assert total<1<<31,'No truncation: output index range exceeded'
            new_digits=1 if final else digits-1
            need=total*(new_digits*4+4+4+(8 if level in retain else 0)+(width*8 if explicit else 0))
            free,_=cp.cuda.runtime.memGetInfo()
            if need>free+cp.get_default_memory_pool().free_bytes():raise MemoryError('Exact pair output exceeds available device memory; no candidates were truncated')
            next_hashes=cp.empty((total,new_digits),cp.uint32);next_min=cp.empty(total,cp.uint32);next_tags=cp.empty(total,cp.int32)
            links=cp.empty((total,2),cp.uint32) if level in retain else self.dummy
            next_vectors=cp.empty((total,width*2),cp.uint32) if explicit else self.dummy
            self.kernels['emit_pairs'](((count+255)//256,),(256,),(sorted_keys,order,minimum,tags,hashes,offsets,vectors,next_hashes,next_min,next_tags,links,next_vectors,
                *[np.int32(x) for x in (count,digits,width,final,bool(regular_size),explicit,level in retain)]))
            if level in retain:parents[level]=links
            hashes,minimum,tags,vectors=next_hashes,next_min,next_tags,next_vectors;width*=2
            cp.cuda.get_current_stream().synchronize();free,_=cp.cuda.runtime.memGetInfo();min_free=min(min_free,free)
            reserved=max(reserved,cp.get_default_memory_pool().total_bytes())
            rounds.append(dict(level=level,input_items=count,output_items=total,retained_parent_bytes=sum(v.nbytes for v in parents.values()),vector_bytes=vectors.nbytes if explicit else 0))
        return parents,vectors,rounds,reserved,min_free,len(hashes)
    def run(self,n,k,seed,mode,regular_size=0,count=None):
        count=count or 1<<(n//(k+1)+1);assert n%8==0 and n%(k+1)==0
        checkpoint=2 if mode=='checkpoint2' else 0;explicit=mode=='vectors'
        gc.collect();cp.get_default_memory_pool().free_all_blocks();cp.cuda.get_current_stream().synchronize();start=time.perf_counter()
        retain=set() if explicit else set(range(checkpoint+1,k+1))
        parents,vectors,rounds,reserved,min_free,final_count=self.forward(n,k,seed,count,k,retain,explicit,regular_size)
        candidates=[];retrieval_passes=0
        if final_count:
            if explicit:candidates=cp.asnumpy(vectors).tolist()
            else:
                needed=list(range(final_count));lookup={}
                for level in range(k,0,-1):
                    nodes=sorted(set(needed))
                    if level in parents:links=parents[level]
                    else:
                        rebuilt,_,_,memory,free,_=self.forward(n,k,seed,count,level,{level},False,regular_size)
                        links=rebuilt[level];reserved=max(reserved,memory);min_free=min(min_free,free);retrieval_passes+=1
                    pairs=cp.asnumpy(links[cp.asarray(nodes,np.uint32)]).tolist();lookup[level]=dict(zip(nodes,pairs))
                    needed=[child for pair in pairs for child in pair]
                    if level not in parents:del rebuilt,links
                def descend(level,index):
                    if not level:return [index]
                    a,b=lookup[level][index];return descend(level-1,a)+descend(level-1,b)
                candidates=[descend(k,index) for index in range(final_count)]
        solve_ms=(time.perf_counter()-start)*1000;validation_start=time.perf_counter();oracle=LeafOracle(n,k,seed,count)
        proofs=set();duplicate_candidates=0;native_codes=[]
        verifier=None
        if (n,k) in ((144,5),(200,9)):
            verifier=ctypes.CDLL(str(pathlib.Path(f'build/libtromp_{n}_{k}.so').resolve()))
            verifier.requant_verify.argtypes=[ctypes.c_uint,ctypes.POINTER(ctypes.c_uint)];verifier.requant_verify.restype=ctypes.c_int
        for chain in candidates:
            if len(set(chain))!=len(chain):duplicate_candidates+=1;continue
            proof=tuple(chain);assert verify(oracle,n,k,proof,regular_size),(n,k,seed,mode,'distinct-leaf tree failed')
            if verifier is not None:
                code=verifier.requant_verify(seed,(ctypes.c_uint*len(proof))(*proof));assert code==0;native_codes.append(code)
            proofs.add(proof)
        if verifier is not None and proofs:
            first=next(iter(proofs));damaged=list(first);damaged[0]=damaged[1]
            assert verifier.requant_verify(seed,(ctypes.c_uint*len(first))(*damaged))!=0
            assert verifier.requant_verify((seed+1)&0xffffffff,(ctypes.c_uint*len(first))(*first))!=0
        verify_ms=(time.perf_counter()-validation_start)*1000
        return dict(n=n,k=k,seed=seed,mode=mode,regular_list_size=regular_size,initial_items=count,rounds=rounds,
            solve_wall_ms=solve_ms,verify_wall_ms=verify_ms,complete_verified_wall_ms=(time.perf_counter()-start)*1000,
            observed_pool_reserved_bytes=reserved,minimum_observed_free_bytes=min_free,retrieval_passes=retrieval_passes,
            raw_candidates=final_count,repeated_index_candidates_rejected=duplicate_candidates,solutions=[list(x) for x in sorted(proofs)],native_verifier_codes=native_codes)

def main():
    assert __debug__
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--seed',type=int,default=20261109)
    parser.add_argument('--full-trials',type=int,default=8);parser.add_argument('--output',default='results/gpu-study.json')
    parser.add_argument('--parameters',default='96,5;144,5;200,9')
    parser.add_argument('--small-only',action='store_true');args=parser.parse_args();solver=Solver();cases=[];validation=[];hash_validation=[]
    for n,k,count in ((24,2,512),(32,3,512),(48,5,512)):
        values=leaves(n,k,args.seed,count);reference,sizes=solve(values,n,k)
        actual=cp.asnumpy(solver.initial(n,k,args.seed,count));bits=n//(k+1)
        expected=np.array([[(v>>(n-(j+1)*bits))&((1<<bits)-1) for j in range(k+1)] for v in values],np.uint32)
        assert np.array_equal(actual,expected)
        for mode in ('vectors','parents','checkpoint2'):
            result=solver.run(n,k,args.seed,mode,count=count);assert result['solutions']==[list(x) for x in reference];validation.append(result)
    for n,k,size,count in ((24,2,256,1024),(48,3,1024,8192),(48,3,4096,32768)):
        values=leaves(n,k,args.seed,count);reference,_=solve(values,n,k,size)
        for mode in ('vectors','parents','checkpoint2'):
            result=solver.run(n,k,args.seed,mode,size,count);assert result['solutions']==[list(x) for x in reference];validation.append(result)
    if not args.small_only:
      for n,k in (tuple(map(int,part.split(','))) for part in args.parameters.split(';')):
       count=1<<(n//(k+1)+1);rng=np.random.default_rng(args.seed+n)
       indices=np.unique(np.concatenate([np.arange(16),np.arange(count-16,count),rng.integers(0,count,4096)]))
       initial=solver.initial(n,k,args.seed,count);actual=cp.asnumpy(initial[cp.asarray(indices)]);oracle=LeafOracle(n,k,args.seed,count);bits=n//(k+1)
       expected=np.array([[(oracle[int(i)]>>(n-(j+1)*bits))&((1<<bits)-1) for j in range(k+1)] for i in indices],np.uint32)
       assert np.array_equal(actual,expected);del initial
       hash_validation.append(dict(n=n,k=k,seed=args.seed,sampled_leaves=len(indices),all_hashlib_leaves_equal=True))
       cpu_reference=None
       if (n,k)==(96,5):cpu_reference=[list(x) for x in solve(leaves(n,k,args.seed),n,k)[0]]
       for trial in range(args.full_trials):
        seed=args.seed+trial;expected=None;modes=('vectors','parents','checkpoint2') if trial%2==0 else ('checkpoint2','parents','vectors')
        for mode in modes:
            result=solver.run(n,k,seed,mode)
            if trial==0 and cpu_reference is not None:assert result['solutions']==cpu_reference
            if expected is None:expected=result['solutions']
            else:assert result['solutions']==expected,(n,k,seed,'memory policy changed accepted solutions')
            cases.append(result);print(n,k,seed,mode,'proofs',len(expected),'ms',round(result['complete_verified_wall_ms'],2),'pool MB',round(result['observed_pool_reserved_bytes']/1e6,2),flush=True)
            progress=pathlib.Path(args.output).with_suffix('.progress.json');temporary=progress.with_suffix('.tmp')
            temporary.write_text(json.dumps(dict(status='in_progress',seed=args.seed,cases=cases),indent=2)+'\n',encoding='utf-8',newline='\n');temporary.replace(progress)
    sources=['gpu_study.py','experiments/birthday.py','cuda/wagner.cu','native/tromp_bridge.cpp']
    record=dict(status='completed',utc=datetime.now(timezone.utc).isoformat(),seed=args.seed,full_trials=args.full_trials,hash_validation=hash_validation,validation=validation,cases=cases,
        source_sha256={p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in sources},
        cubin_sha256=hashlib.sha256(pathlib.Path('build/wagner.cubin').read_bytes()).hexdigest(),
        scope='Canonical 140-byte Equihash header, BLAKE2b digest length floor(512/n)*n/8, exact all-pairs joins without bucket caps. Repeated-index candidates rejected by independent CPU verifier; accepted standard-parameter proofs checked by pinned Tromp native verifier. Checkpoint mode selectively rebuilds discarded early parent levels. Complete verified timer includes hashing, dynamic allocations, sorting, reconstruction, transfers and independent verification. Regular-list experiments model the mathematical constraint and do not implement a deployed Requihash protocol. Independent nonces retained; no energy or network submission.')
    pathlib.Path(args.output).write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')

if __name__=='__main__':main()
