# Results and evidence

A research project by [Requant Network](https://requant.network).

| Evidence | Role |
| --- | --- |
| [CPU controls](results/cpu-study.json) | Exact small single/regular searches, altered-proof rejection, exhaustive tiny trees. |
| [Canonical primary](results/gpu-study.json), [independent replication](results/gpu-independent-replication.json) | Eight disjoint nonces/cohort, three parameters, all three policies, every proof and round count. |
| [Earlier repeat control](results/gpu-replication.json) | Seven nonces overlap the primary; retained for repeatability, not an independent eight-nonce cohort. |
| [Latency primary](results/latency-study.json), [second header](results/latency-replication.json) | Five warm-ups/thirty observations, explicit solve/verify/complete scopes. |
| [Allocator primary](results/allocator-study.json), [second header](results/allocator-replication.json) | Checkpoint recomputation with unused-pool release versus the original and parents. |
| [Artifact preflight](results/author-preflight.json) | One nonce/parameter diagnostic with original assertion-only harness. |
| [Artifact primary](results/author-study.json), [replication](results/author-replication.json) | Complete native time/RSS campaign; all chains retained, duplicate-index outcomes rejected. |
| [Matched lists primary](results/regular-study.json), [replication](results/regular-replication.json) | Same leaves/count in single/regular comparisons; complete CPU/GPU set equality. |
| [Stochastic table](results/stochastic-summary.csv) | Accepted rates, zero-yield nonces, rejected candidates, median/p95 and resource observations. |
| [Latency table](results/latency-summary.csv), [regular table](results/regular-summary.csv) | Separate fixed-input/matched-workload summaries. |
| [Native build](results/native-build.json), [final bindings](results/build.json), [environment](results/environment.json) | Upstream/compiler/binary/source/raw provenance and disclosed compatibility fix. |

The [final report](FINAL_REPORT.md) states the practical decisions and limits. No energy, network deployment, profitability or new asymptotic-security result is implied.
