"""CPU-only independent replay of retained canonical and artifact collision trees."""
import hashlib,json,pathlib,struct
from author_study import artifact_values
from experiments.birthday import header,verify,leaves,solve

class Oracle:
    def __init__(self,n,k,seed,count):self.n=n;self.k=k;self.seed=seed;self.count=count;self.cache={}
    def __len__(self):return self.count
    def __getitem__(self,index):
        per=512//self.n;group=index//per;size=self.n//8
        if group not in self.cache:
            self.cache[group]=hashlib.blake2b(header(self.seed)+struct.pack('<I',group),digest_size=per*size,
                person=b'ZcashPoW'+struct.pack('<II',self.n,self.k)).digest()
        raw=self.cache[group];start=index%per*size;return int.from_bytes(raw[start:start+size],'big')

class Sparse(dict):
    def __len__(self):return self.count

total=0;rejected=0;oracles={};sets={};complete={}
for path in sorted(pathlib.Path('results').glob('*.json')):
    if path.name in ('native-build.json','build.json','environment.json','cpu-study.json'):continue
    r=json.loads(path.read_text());assert r.get('status','completed')=='completed',path
    artifact=path.name.startswith('author-')
    for case in r.get('validation',[])+r.get('cases',[]):
        n,k,seed=case['n'],case['k'],case['seed'];regular=case.get('regular_list_size',0)
        count=case.get('initial_items',1<<(n//(k+1)+1));key=(artifact,n,k,seed,regular,count)
        if not artifact and key not in oracles:oracles[key]=Oracle(n,k,seed,count)
        accepted=[]
        flags=case.get('independent_collision_trees_valid',True)
        for i,chain in enumerate(case['solutions']):
            if artifact:
                values=Sparse(artifact_values(n,k,seed,chain));values.count=count
                valid=verify(values,n,k,chain)
                expected=flags[i] if isinstance(flags,list) else flags
                assert valid==expected,(path,n,k,seed,i)
                xor=0
                for index in chain:xor^=values[index]
                assert xor==0
                if not valid:
                    assert len(set(chain))<len(chain);rejected+=1;continue
            else:
                values=oracles[key];assert verify(values,n,k,chain,regular),(path,n,k,seed)
            damaged=list(chain);damaged[0]=damaged[1];assert not verify(values,n,k,damaged,regular)
            accepted.append(tuple(chain));total+=1
        normalized=sorted(accepted);assert len(normalized)==len(set(normalized))
        if key in sets:assert sets[key]==normalized,(path,key,'accepted set differs')
        else:sets[key]=normalized
        if artifact:
            assert all(code!=0 for code in case['canonical_network_verifier_codes'])
            if isinstance(flags,list):
                assert case['accepted_solution_count']==sum(flags)
                assert case['rejected_duplicate_count']==len(flags)-sum(flags)
        elif 'native_verifier_codes' in case:assert all(code==0 for code in case['native_verifier_codes'])
        if (path.name.startswith('regular-') or regular or n<=48) and not artifact:
            if key not in complete:complete[key]=solve(leaves(n,k,seed,count),n,k,regular)[0]
            assert normalized==complete[key],(path,key,'CPU solution set differs')
print(total,'retained accepted proofs independently verified;',rejected,'duplicate-index artifact chains rejected; negative controls passed')
