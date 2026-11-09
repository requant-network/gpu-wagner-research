"""Bind canonical GPU evidence and author/native metadata to executed sources."""
import hashlib,json,pathlib,subprocess

digest=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
names=['gpu-study.json','gpu-independent-replication.json','gpu-replication.json','latency-study.json','latency-replication.json',
    'allocator-study.json','allocator-replication.json','regular-study.json','regular-replication.json',
    'author-study.json','author-replication.json','author-preflight.json','native-build.json']
cubin=digest('build/wagner.cubin')
for name in names[:3]:assert json.loads(pathlib.Path('results',name).read_text())['cubin_sha256']==cubin
native=json.loads(pathlib.Path('results/native-build.json').read_text())
for key,build in native['builds'].items():
    assert digest(f'build/author_{key}')==build['author_binary_sha256']
    assert digest(f'build/libtromp_{key}.so')==build['verifier_binary_sha256']
record=dict(nvcc=subprocess.check_output(['/usr/local/cuda-13.3/bin/nvcc','--version'],text=True).strip(),
    cuda_flags=['-O3','-std=c++17','-arch=sm_120','-cubin'],cubin_sha256=cubin,
    source_sha256={p:digest(p) for p in ('collect_build.py','cuda/wagner.cu','native/author_bench.cpp','native/tromp_bridge.cpp')},
    result_sha256={p:digest(pathlib.Path('results',p)) for p in names},
    scope='Post-run measured binary/source/raw bindings. Native compiler, flags and exact upstream pins are in native-build.json, including the documented Tromp alignment-only compatibility patch. Binary hashes identify these builds; rebuilds need not be byte-identical.')
pathlib.Path('results/build.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
