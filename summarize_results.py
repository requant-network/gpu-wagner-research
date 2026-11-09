"""Derive separate stochastic, fixed-input and matched-list evidence tables."""
import csv,json,math,pathlib,statistics

def write(name,rows):
    with pathlib.Path('results',name).open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)

def p95(values):return sorted(values)[math.ceil(.95*len(values))-1]

rows=[]
for stem in ('gpu-study','gpu-independent-replication','gpu-replication','author-study','author-replication'):
    record=json.loads(pathlib.Path(f'results/{stem}.json').read_text());groups={}
    for c in record['cases']:groups.setdefault((c['n'],c['k'],c.get('mode',c.get('height'))),[]).append(c)
    for (n,k,policy),cases in groups.items():
        author=stem.startswith('author');times=[c['solve_wall_ms'] if author else c['complete_verified_wall_ms'] for c in cases]
        accepted=[c.get('accepted_solution_count',len(c['solutions'])) for c in cases]
        rows.append(dict(campaign=stem,base_seed=record['seed'],n=n,k=k,policy=policy,nonces=len(cases),accepted=sum(accepted),
            zero_accepted_nonces=accepted.count(0),rejected_duplicate_chains=sum(c.get('rejected_duplicate_count',c.get('repeated_index_candidates_rejected',0)) for c in cases),
            median_ms=f'{statistics.median(times):.6f}',p95_ms=f'{p95(times):.6f}',
            aggregate_accepted_per_second=f'{sum(accepted)*1000/sum(times):.6f}',
            maximum_observed_pool_bytes='' if author else max(c['observed_pool_reserved_bytes'] for c in cases),
            maximum_process_rss_kib=max(c['peak_rss_kib'] for c in cases) if author else '',
            timer='native_solve_reconstruct' if author else 'complete_verified'))
write('stochastic-summary.csv',rows)
rows=[]
for stem in ('latency-study','latency-replication','allocator-study','allocator-replication'):
    record=json.loads(pathlib.Path(f'results/{stem}.json').read_text())
    for c in record['cases']:
        for mode,scopes in c['samples'].items():
            for scope,values in scopes.items():
                assert len(values)==30 and all(math.isfinite(v) and v>0 for v in values)
                rows.append(dict(campaign=stem,seed=record['seed'],n=c['n'],k=c['k'],policy=mode,accepted=len(c['solutions']),
                    scope=scope,samples=len(values),median=f'{statistics.median(values):.6f}',p95=f'{p95(values):.6f}',
                    maximum_observed_pool_bytes=c.get('observed_pool_reserved_bytes',{}).get(mode,'')))
write('latency-summary.csv',rows)
rows=[]
for stem in ('regular-study','regular-replication'):
    record=json.loads(pathlib.Path(f'results/{stem}.json').read_text())
    for c in record['cases']:
        v=c['samples_ms'];assert len(v)==30
        rows.append(dict(campaign=stem,seed=record['seed'],n=c['n'],k=c['k'],initial_items=c['initial_items'],
            regular_list_size=c['regular_list_size'],accepted=len(c['solutions']),cpu_round_sizes=':'.join(map(str,c['cpu_round_sizes'])),
            gpu_round_sizes=':'.join(str(x['output_items']) for x in c['rounds']),median_verified_ms=f'{statistics.median(v):.6f}',
            p95_verified_ms=f'{p95(v):.6f}',observed_pool_bytes=c['observed_pool_reserved_bytes']))
write('regular-summary.csv',rows)
print('Stochastic, fixed-input and matched-list summaries regenerated')
