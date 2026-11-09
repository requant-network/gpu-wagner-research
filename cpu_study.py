"""Exact small-instance single-list and regular-list birthday checks."""
import argparse,hashlib,itertools,json,pathlib,random
from experiments.birthday import canonical,leaves,solve,verify

def main():
    assert __debug__
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',default='results/cpu-study.json');args=parser.parse_args()
    cases=[];negatives=0
    for n,k,count in ((16,1,512),(24,2,512),(32,3,512),(48,5,512)):
        for seed in (20261109,20261110):
            values=leaves(n,k,seed,count);solutions,sizes=solve(values,n,k)
            if k==1:
                exhaustive=sorted((i,j) for i in range(count) for j in range(i+1,count) if values[i]==values[j])
                assert solutions==exhaustive
            for chain in solutions:
                assert verify(values,n,k,chain)
                assert not verify(values,n,k,(chain[0],)*len(chain));negatives+=1
                assert not verify(values,n,k,chain[::-1]);negatives+=1
            cases.append(dict(n=n,k=k,seed=seed,kind='single_list',sizes=sizes,solutions=[list(x) for x in solutions]))
    for seed in (20261109,20261110):
        n,k,size=24,2,256;values=leaves(n,k,seed,4*size);solutions,sizes=solve(values,n,k,size)
        assert all(verify(values,n,k,c,size) for c in solutions)
        cases.append(dict(n=n,k=k,seed=seed,kind='regular_lists',list_size=size,sizes=sizes,solutions=[list(x) for x in solutions]))
    # Exhaust every possible four-leaf candidate on a tiny fixture, including tree constraints.
    rng=random.Random(8675309);values=[rng.randrange(512) for _ in range(16)];expected=set()
    for indices in itertools.combinations(range(16),4):
        a=indices[0]
        for mate in indices[1:]:
            rest=[i for i in indices if i not in (a,mate)];chain=canonical((a,mate,*rest))
            if verify(values,9,2,chain):expected.add(chain)
    actual,_=solve(values,9,2);assert set(actual)==expected
    result=dict(cases=cases,negative_checks=negatives,exhaustive_four_leaf_trees=True,
        source_sha256={p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in ('cpu_study.py','experiments/birthday.py')},
        scope='Canonical BLAKE2b leaves, exact collision trees, no list-capacity truncation. Regular-list fixtures study the mathematical constraint, not a deployed Requihash protocol.')
    pathlib.Path(args.output).parent.mkdir(parents=True,exist_ok=True);pathlib.Path(args.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(len(cases),'complete small-instance searches;',negatives,'altered proofs rejected')

if __name__=='__main__':main()
