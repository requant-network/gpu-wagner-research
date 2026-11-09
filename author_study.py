"""Reproduce artifact time/memory trade-offs with independent solution checks."""
import argparse,ctypes,hashlib,json,pathlib,struct,subprocess,tempfile,time
from datetime import datetime,timezone
from experiments.birthday import canonical,header,verify

def artifact_values(n,k,seed,indices):
    size=n//8;prefix=header(seed)+bytes(32);person=b'ZcashPoW'+struct.pack('<II',n,k);cache={};result={}
    for index in indices:
        group=index//2
        if group not in cache:cache[group]=hashlib.blake2b(prefix+struct.pack('<I',group),digest_size=50,person=person).digest()
        start=index%2*size;raw=cache[group][start:start+size]
        # The artifact consumes low bits of each byte first; normalize to MSB-prefix order.
        result[index]=int.from_bytes(bytes(int(f'{byte:08b}'[::-1],2) for byte in raw),'big')
    return result

def main():
    assert __debug__
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--seed',type=int,default=20261109)
    parser.add_argument('--trials',type=int,default=8);parser.add_argument('--output',default='results/author-study.json');args=parser.parse_args()
    cases=[]
    for n,k,heights in ((144,5,(0,3,4)),(200,9,(0,5,8))):
        verifier=ctypes.CDLL(str(pathlib.Path(f'build/libtromp_{n}_{k}.so').resolve()))
        verifier.requant_verify.argtypes=[ctypes.c_uint,ctypes.POINTER(ctypes.c_uint)];verifier.requant_verify.restype=ctypes.c_int
        reference_sets={}
        for trial in range(args.trials):
            seed=args.seed+trial;order=heights if trial%2==0 else heights[::-1]
            for height in order:
                output=pathlib.Path('build/author-result.json');started=time.perf_counter()
                subprocess.run([f'./build/author_{n}_{k}',str(seed),str(height),str(output)],check=True,stdout=subprocess.DEVNULL)
                process_wall=(time.perf_counter()-started)*1000;case=json.loads(output.read_text());proofs=[];network_codes=[]
                for chain in case['solutions']:
                    chain=canonical(chain);values=artifact_values(n,k,seed,chain)
                    # A sparse value mapping suffices for the independent recursive verifier.
                    class Sparse(dict):
                        def __len__(self):return 1<<(n//(k+1)+1)
                    assert verify(Sparse(values),n,k,chain),(n,k,seed,height)
                    code=verifier.requant_verify(seed,(ctypes.c_uint*len(chain))(*chain));network_codes.append(code);proofs.append(list(chain))
                normalized=sorted(map(tuple,proofs));assert len(normalized)==len(set(normalized))
                if seed in reference_sets:assert normalized==reference_sets[seed],(n,k,seed,height,'solution set changed')
                else:reference_sets[seed]=normalized
                case.update(solutions=proofs,independent_collision_trees_valid=True,canonical_network_verifier_codes=network_codes,process_wall_ms=process_wall)
                cases.append(case);print(n,k,seed,height,'solutions',len(proofs),'ms',round(case['solve_wall_ms'],2),'rss',case['peak_rss_kib'],flush=True)
    sources=['author_study.py','experiments/birthday.py','native/author_bench.cpp','native/tromp_bridge.cpp']
    record=dict(utc=datetime.now(timezone.utc).isoformat(),seed=args.seed,trials=args.trials,cases=cases,
        source_sha256={p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in sources},
        scope='Pinned TCHES artifact, complete function allocation/solve/reconstruction timer, fresh process per nonce/height. Python independently checks every distinct-index collision tree using the artifact 172-byte prefix, digest length 50, two slices per digest and LSB-first bit order within bytes. Canonical Tromp verifier tested separately on each proof. No comparison of artifact throughput with a different hash convention. No fixed-input warm-up policy: independent stochastic inputs, all outcomes retained.')
    pathlib.Path(args.output).write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')

if __name__=='__main__':main()
