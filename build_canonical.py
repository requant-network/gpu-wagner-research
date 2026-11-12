"""Compile the pinned optimized canonical CPU solver without changing its algorithm."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

REVISION='fab686ed3fac49dfd22624851025f31856728517'


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('upstream',type=Path);args=parser.parse_args()
    assert subprocess.check_output(['git','-C',str(args.upstream),'rev-parse','HEAD'],text=True).strip()==REVISION
    compat=Path('build/tromp-compat');assert (compat/'equi_miner.h').read_bytes()==(args.upstream/'equi_miner.h').read_bytes()
    builds={}
    for n,k in ((144,5),(200,9)):
        for threads in (1,6):
            flags=['-O3','-std=c++17','-march=native','-UNDEBUG','-pthread',f'-DWN={n}',f'-DWK={k}']
            # Match the artifact's provided1445 target; keep2009's specialized default.
            if n==144:flags+=['-DRESTBITS=4']
            if threads>1:flags+=['-DATOMIC']
            target=Path('build')/f'canonical_{n}_{k}_{threads}'
            subprocess.run(['g++',*flags,'-I'+str(compat),'native/canonical_bench.cpp',str(compat/'blake/blake2b.cpp'),'-o',str(target)],check=True)
            builds[f'{n}_{k}_{threads}']=dict(flags=flags,binary_sha256=hashlib.sha256(target.read_bytes()).hexdigest())
    record=dict(revision=REVISION,builds=builds,
                source_sha256={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ('build_canonical.py','native/canonical_bench.cpp')},
                upstream_source_sha256={p:hashlib.sha256((args.upstream/p).read_bytes()).hexdigest() for p in ('equi.h','equi_miner.h')},
                compatibility='Existing disclosed alignment-only build copy from build_native.py; algorithm and verifier unchanged. Single-thread build omits atomics; six-thread build uses upstream atomics. Bucket/hash filters and8-solution output cap remain and must be reported.')
    Path('results/canonical-build.json').write_text(json.dumps(record,indent=2)+'\n')


if __name__=='__main__':main()
