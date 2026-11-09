"""Optional publication figure from fixed-input raw data; requires Matplotlib."""
import json,pathlib,statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({'font.size':10,'svg.hashsalt':'requant-wagner-20261109'})
fig,axes=plt.subplots(1,2,figsize=(11,4.6))
for axis,(n,k) in zip(axes,((144,5),(200,9))):
    for name,color,style in (('latency-study','#145da0','-'),('latency-replication','#b75519','--')):
        r=json.loads(pathlib.Path(f'results/{name}.json').read_text());c=next(c for c in r['cases'] if (c['n'],c['k'])==(n,k))
        modes=('vectors','parents','checkpoint2');x=[c['observed_pool_reserved_bytes'][m]/1e9 for m in modes]
        y=[statistics.median(c['samples'][m]['complete_verified_wall_ms']) for m in modes]
        axis.plot(x,y,marker='o',color=color,linestyle=style,label=f"Seed {r['seed']}; {len(c['solutions'])} proofs")
        for i,m in enumerate(modes):
            offset=(0,10 if name=='latency-study' else -17);align='center'
            if n==144 and name=='latency-replication' and m!='vectors':
                offset=(-6,-22) if m=='checkpoint2' else (8,-22);align='right' if m=='checkpoint2' else 'left'
            if n==200 and m!='vectors':
                offset=(12,12 if m=='checkpoint2' else -7) if name=='latency-study' else (15,-18 if m=='checkpoint2' else -22);align='left'
            axis.annotate(m,(x[i],y[i]),xytext=offset,textcoords='offset points',ha=align,fontsize=8,color=color)
    axis.set(title=f'Canonical Equihash ({n},{k})',xlabel='Maximum observed reserved pool (decimal GB)',ylabel='Median complete verified wall time (ms)')
    axis.grid(alpha=.2);axis.margins(x=.17,y=.25);axis.legend(loc='best',fontsize=8)
fig.suptitle('Requant Network: measured GPU time and memory',fontsize=14)
fig.text(.5,.025,'RTX 5060 Ti | 5 warm-ups, 30 repeats per fixed header | Different headers have different reconstruction work',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.065,1,.95));pathlib.Path('build').mkdir(exist_ok=True)
fig.savefig('results/time-memory.svg',metadata={'Date':None,'Creator':'Requant Network / Matplotlib'})
fig.savefig('build/time-memory.png',dpi=150);plt.close(fig)
