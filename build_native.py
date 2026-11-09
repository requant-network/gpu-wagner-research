"""Build unchanged upstream CPU algorithms and canonical verifier wrappers."""
import argparse,hashlib,json,pathlib,shutil,subprocess
AUTHOR='e53d92c7988bcb6868d702d44f15114e67e18c30'
TROMP='fab686ed3fac49dfd22624851025f31856728517'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('author',type=pathlib.Path);parser.add_argument('tromp',type=pathlib.Path);args=parser.parse_args()
for path,revision in ((args.author,AUTHOR),(args.tromp,TROMP)):
    assert subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()==revision
    assert not subprocess.check_output(['git','-C',str(path),'status','--porcelain'],text=True).strip()
pathlib.Path('build').mkdir(exist_ok=True);builds={}
compat=pathlib.Path('build/tromp-compat');shutil.copytree(args.tromp,compat,dirs_exist_ok=True,ignore=shutil.ignore_patterns('.git'))
old=(compat/'blake/blake2.h').read_text();assert old.count('ALIGN( 64 ) typedef struct')==4
new=old.replace('ALIGN( 64 ) typedef struct','typedef struct ALIGN( 64 )')
(compat/'blake/blake2.h').write_text(new,encoding='utf-8',newline='\n')
for n,k in ((144,5),(200,9)):
    flags=['-O3','-std=c++17','-march=native','-UNDEBUG']
    include=['-I'+str(args.author/'advanced-cip/include'),'-I'+str(args.author/'third_party/blake'),'-I'+str(args.author/'third_party/blake2-avx2'),'-I'+str(args.author/'third_party/kxsort')]
    executable=f'build/author_{n}_{k}'
    command=['g++',*flags,*include,*(['-DPARAM_200'] if n==200 else []),'native/author_bench.cpp',str(args.author/f'advanced-cip/src/eq{n}_{k}/apr_alg.cpp'),str(args.author/'third_party/blake/blake2b.cpp'),'-o',executable]
    subprocess.run(command,check=True)
    library=f'build/libtromp_{n}_{k}.so'
    subprocess.run(['g++','-O3','-std=c++17','-shared','-fPIC',f'-DWN={n}',f'-DWK={k}','-I'+str(compat),'native/tromp_bridge.cpp',str(compat/'blake/blake2b.cpp'),'-o',library],check=True)
    builds[f'{n}_{k}']=dict(author_flags=flags,author_binary_sha256=hashlib.sha256(pathlib.Path(executable).read_bytes()).hexdigest(),verifier_binary_sha256=hashlib.sha256(pathlib.Path(library).read_bytes()).hexdigest())
sources=['build_native.py','native/author_bench.cpp','native/tromp_bridge.cpp']
record=dict(author_revision=AUTHOR,tromp_revision=TROMP,gxx=subprocess.check_output(['g++','--version'],text=True).splitlines()[0],builds=builds,
    tromp_compatibility_fix='Move four alignment attributes from typedef to struct for modern GCC. Verifier and hash arithmetic bodies unchanged.',
    original_blake_header_sha256=hashlib.sha256((args.tromp/'blake/blake2.h').read_bytes()).hexdigest(),compatible_blake_header_sha256=hashlib.sha256((compat/'blake/blake2.h').read_bytes()).hexdigest(),
    source_sha256={p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in sources},
    scope='Original wrappers, unchanged upstream algorithms and verifier. CPU artifact hash convention is separately checked; binary hashes are informational and rebuilds need not be byte-identical.')
pathlib.Path('results/native-build.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
