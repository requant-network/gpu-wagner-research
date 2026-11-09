"""Validate campaign coverage, independent nonce cohorts and timing samples."""
import json,math,pathlib

def read(stem):return json.loads(pathlib.Path(f'results/{stem}.json').read_text())

for a,b,author in (('gpu-study','gpu-independent-replication',False),('author-study','author-replication',True)):
    first,second=read(a),read(b)
    assert first['status']==second['status']=='completed'
    assert not {c['seed'] for c in first['cases']}&{c['seed'] for c in second['cases']},'Independent cohorts must not reuse nonces'
    for r in (first,second):
        assert len(r['cases'])==(48 if author else 72)
        for n,k in (((144,5),(200,9)) if author else ((96,5),(144,5),(200,9))):
            cases=[c for c in r['cases'] if (c['n'],c['k'])==(n,k)]
            assert len(cases)==24 and len({c['seed'] for c in cases})==8
            expected=set((0,3,4) if n==144 else (0,5,8)) if author else {'vectors','parents','checkpoint2'}
            for seed in {c['seed'] for c in cases}:
                matching=[c for c in cases if c['seed']==seed]
                assert len(matching)==3 and {c['height'] if author else c['mode'] for c in matching}==expected
            for c in cases:
                assert c['solve_wall_ms']>0
                if author:assert c['process_wall_ms']>=c['solve_wall_ms'] and c['peak_rss_kib']>0
                else:
                    assert c['complete_verified_wall_ms']>=c['solve_wall_ms']
                    assert c['raw_candidates']>=len(c['solutions'])
                    assert c['raw_candidates']-c['repeated_index_candidates_rejected']>=len(c['solutions'])
        if not author:assert len(r['hash_validation'])==3 and all(4000<=c['sampled_leaves']<=4128 and c['all_hashlib_leaves_equal'] for c in r['hash_validation'])
for stem,count in (('latency-study',3),('latency-replication',3),('allocator-study',2),('allocator-replication',2)):
    r=read(stem);assert r['status']=='completed' and r['warmups']==5 and r['samples']==30 and len(r['cases'])==count
    for c in r['cases']:
        for scopes in c['samples'].values():
            for values in scopes.values():assert len(values)==30 and all(math.isfinite(v) and v>0 for v in values)
for stem in ('regular-study','regular-replication'):
    r=read(stem);assert r['status']=='completed' and len(r['cases'])==6
    for c in r['cases']:
        assert c['cpu_and_gpu_solution_sets_equal'] and len(c['samples_ms'])==30
        assert all(math.isfinite(v) and v>0 for v in c['samples_ms'])
print('Independent cohorts, required parameters and fixed-input/matched-list coverage passed')
