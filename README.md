# GPU Wagner Research

Exact generalized-birthday search, Equihash memory/time trade-offs and regular-list comparisons.

A research project by [Requant Network](https://requant.network).

**Status: completed bounded research campaign, with independent nonce cohorts.**

An exact consumer-GPU solver completes canonical Equihash(144,5) and (200,9).
Parent pointers reduce memory substantially; checkpoint reconstruction remains
input- and allocator-dependent. The pinned CPU artifact is checked under its
own hash convention, with repeated-index candidates explicitly rejected.

- [Final report and reproduction](FINAL_REPORT.md)
- [Methods](METHODS.md) and [evidence map](RESULTS.md)
- [Stochastic summaries](results/stochastic-summary.csv), [fixed-input latency](results/latency-summary.csv), [matched-list comparisons](results/regular-summary.csv)

CPU replay: `python cpu_study.py --output build/ci.json`,
`python verify_proofs.py`, `python verify_campaigns.py`, `python verify_results.py`
and `python summarize_results.py`.

See [RESEARCH.md](RESEARCH.md) for the committed experimental scope. Original code is MIT licensed; upstream sources retain their own licenses.
