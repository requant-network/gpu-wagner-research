"""Independent proof checking for the optimized matching canonical CPU baseline."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
from experiments.birthday import verify,header
import struct

class LeafOracle:
    def __init__(self,n,k,seed,count):self.n,self.k,self.seed,self.count,self.cache=n,k,seed,count,{}
    def __len__(self):return self.count
    def __getitem__(self,index):
        per=512//self.n;group=index//per;size=self.n//8
        if group not in self.cache:self.cache[group]=hashlib.blake2b(header(self.seed)+struct.pack("<I",group),digest_size=per*size,person=b"ZcashPoW"+struct.pack("<II",self.n,self.k)).digest()
        start=index%per*size;return int.from_bytes(self.cache[group][start:start+size],"big")



def main():
    assert __debug__
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--seed',type=int,default=2026111200)
    parser.add_argument('--trials',type=int,default=8);parser.add_argument('--output',default='results/canonical-cpu-study.json')
    args=parser.parse_args();cases=[];build_path=Path('results/canonical-build.json');build=json.loads(build_path.read_text())
    for n,k in ((144,5),(200,9)):
        for trial in range(args.trials):
            seed=args.seed+trial
            for threads in ((1,6) if trial%2==0 else (6,1)):
                binary=Path('build')/f'canonical_{n}_{k}_{threads}'
                assert hashlib.sha256(binary.read_bytes()).hexdigest()==build['builds'][f'{n}_{k}_{threads}']['binary_sha256']
                start=time.perf_counter()
                try:run=subprocess.run([str(binary),str(seed),str(threads)],capture_output=True,text=True,timeout=600)
                except subprocess.TimeoutExpired as error:
                    output=error.stdout or ''
                    if isinstance(output,bytes):output=output.decode(errors='replace')
                    run=subprocess.CompletedProcess([str(binary)],124,stdout=output,stderr='timeout after600s')
                process_ms=(time.perf_counter()-start)*1000
                lines=run.stdout.splitlines();results=[line[7:] for line in lines if line.startswith('RESULT ')]
                case=dict(n=n,k=k,seed=seed,threads=threads,exit_code=run.returncode,process_wall_ms=process_ms,
                          bucket_reports=[dict(bucket_full=int(a),zero_tail_filtered=int(b)) for a,b in re.findall(r' b(\d+) h(\d+)',run.stdout)])
                if run.returncode==0:
                    assert len(results)==1;value=json.loads(results[0]);oracle=LeafOracle(n,k,seed,1<<(n//(k+1)+1))
                    valid=[]
                    for proof in value['solutions']:
                        try:valid.append(bool(verify(oracle,n,k,proof)))
                        except (AssertionError,IndexError,ValueError):valid.append(False)
                    value['proof_validity']=valid
                    value['all_retained_proofs_independently_valid']=all(valid)
                    value['duplicate_returned_proofs']=len(value['solutions'])-len({tuple(p) for p in value['solutions']})
                    value['output_cap_reached']=value['raw_solution_count']>len(value['solutions'])
                    case['result']=value
                else:case['last_line']=lines[-1] if lines else ''
                cases.append(case)
                record=dict(utc=datetime.now(timezone.utc).isoformat(),seed=args.seed,trials=args.trials,cases=cases,
                            source_sha256={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in
                                ('canonical_cpu_study.py','build_canonical.py','native/canonical_bench.cpp','gpu_study.py','experiments/birthday.py')},
                            result_sha256={build_path.name:hashlib.sha256(build_path.read_bytes()).hexdigest()},
                            scope='Same canonical140-byte header, nonce offset108, BLAKE2b parameters and recursive proof contract as GPU. Each nonce gets one fresh process per1/6-thread solver; these are independent nonce observations, not30 repetitions of one input. Complete process wall and internal allocation/solve/reconstruction timers separated. Every retained proof rechecked independently. Upstream bucket limits, last32-bit filter and8-output cap remain; counters and cross-solver set differences prevent completeness or equal-work claims.')
                Path(args.output).write_text(json.dumps(record,indent=2)+'\n')
                print(n,k,seed,threads,'exit',run.returncode,'proofs',len(case.get('result',{}).get('solutions',[])),flush=True)


if __name__=='__main__':main()
