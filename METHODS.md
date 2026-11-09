# Methods

A research project by [Requant Network](https://requant.network).

The [final report](FINAL_REPORT.md) defines both hash conventions, all timing/memory boundaries, pins, commands and limits. Canonical GPU experiments and the pinned CPU artifact solve different hash-defined puzzles; their throughput is not compared as if the inputs matched.

The independent reference uses hashlib BLAKE2b, arbitrary-precision integers and exhaustive small-instance collision-tree searches. GPU joins enumerate exact pair counts with 64-bit scans; overflow or insufficient memory fails explicitly. Standard-parameter proofs pass native Tromp at runtime, and all retained proofs can be replayed with the independent CPU oracle in `verify_proofs.py`. Full-parameter native acceptance verifies validity, while complete solution-set equality is independently checked on small instances and matched regular-list workloads.

Two principal eight-nonce cohorts have disjoint seed ranges. The earlier overlapping run remains a repeat control, explicitly excluded from independent-cohort claims. All zero-yield nonces, raw candidate counts and duplicate rejections remain in rate denominators. Accepted rate is sum(accepted)/sum(wall time), not the reciprocal of a successful-only median.

Fixed-input GPU studies use five warm-ups and thirty measurements; alternating order reduces ordering effects. p95 is nearest rank ceil(0.95n)-1, descriptive with these sample sizes. Checkpoint rebuilding occurs only when raw final candidates exist, so latency is input-dependent. The allocator follow-up changes only unused-block release and times its cost. The CPU artifact uses fresh processes and independent nonces, with process RSS separate from algorithm wall time. GPU pool samples and CPU RSS are distinct resource metrics.

Hashes bind executed source, binaries and raw evidence. CPU CI checks reference arithmetic, retained proof validity, coverage and derived tables without requiring CUDA. It cannot authenticate a historical timing trace merely from a source hash. Dynamic clocks and OS activity remain uncontrolled; energy and mining economics were not measured.
