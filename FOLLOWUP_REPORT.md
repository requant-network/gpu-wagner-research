# Canonical CPU, memory policies and independent nonces

Requant Network, 12 November 2026. This supplement closes the comparator, checkpoint-depth, bounded-index and larger-cohort questions from the [historical report](FINAL_REPORT.md).

## Comparable canonical workload

The added native comparator uses the pinned optimized Tromp algorithm, with its original header hashing, bucket algorithm and specialized parameter choices. It receives exactly the GPU experiment's canonical 140-byte header and nonce at byte offset 108. The single-thread build avoids atomics; the six-thread build uses the upstream atomic path. Only the previously disclosed alignment compatibility changes remain. This is not the incompatible artifact-header comparison from the preliminary study.

Two disjoint cohorts each contain eight CPU nonces per parameter/thread count. The GPU stochastic cohort contains those same eight plus 24 further nonces. Each CPU nonce gets one fresh process, not thirty repeated timings of the same input. Every returned proof is checked independently. The native bucket limits, last-32-bit filter and eight-output cap remain visible; observed bucket-drop counters are retained and multithreaded diagnostic counters are not a formal completeness certificate.

Medians for **the same eight nonces** per cohort, milliseconds. CPU process wall includes allocation, solve and reconstruction, but excludes the later Python proof replay. GPU verified wall includes independent CPU/native verification; its separate solve boundary is shown to avoid silently equating different timers.

| Cohort | Parameters | CPU 1 thread process | CPU 6 threads process | GPU parents solve | GPU parents verified |
| --- | --- | ---: | ---: | ---: | ---: |
| 2026111200 | (144,5) | 11719.073 | 3223.548 | 341.019 | 341.324 |
| 2026111200 | (200,9) | 491.329 | 159.835 | 33.592 | 36.932 |
| 2026121200 | (144,5) | 14754.464 | 3520.625 | 341.876 | 342.290 |
| 2026121200 | (200,9) | 496.904 | 172.302 | 33.308 | 35.505 |

All retained CPU/GPU solution sets match on these common nonces, and all CPU proofs are independently valid with no duplicate returned proofs. Some (144,5) upstream bucket-drop counters are nonzero, so matching these observed sets is not a general theorem that the capped CPU solver enumerates every mathematical solution. The GPU implementation continues to emit exact joins without adding bucket truncation.

## Fixed-input checkpoint and packing policies

Each of two fixed headers per parameter is measured with five warm-ups and thirty repetitions, alternating policy order. Checkpoints discard the first one/two/three parent levels and reconstruct them when required. The packed policy converts a link array to 24 bits **only after its maximum child index is below 2^24**; otherwise it retains all 32 bits. Conversion, maximum-index synchronization, unpacking, reconstruction and allocator cache release are inside the complete timer. Preflight tests include 8,192 gathered values, the largest 24-bit value and a mandatory overflow fallback.

Selected complete verified medians and maximum **observed** allocator reservation. These reservation snapshots are not a true instantaneous whole-device peak; sorting/reconstruction lifetimes can prevent a monotonic checkpoint-memory ranking.

| Seed | Parameters | Policy | Verified median, ms | Max observed pool, MiB |
| --- | --- | --- | ---: | ---: |
| 2026111200 | (144,5) | parents | 341.005 | 4244.7 |
| 2026111200 | (144,5) | checkpoint1 | 429.896 | 3988.7 |
| 2026111200 | (144,5) | checkpoint2 | 589.504 | 4756.1 |
| 2026111200 | (144,5) | checkpoint3 | 813.069 | 4238.1 |
| 2026111200 | (144,5) | packed_parents | 350.364 | 3725.9 |
| 2026111200 | (144,5) | packed_checkpoint2 | 602.647 | 4237.6 |
| 2026111200 | (200,9) | parents | 35.824 | 516.5 |
| 2026111200 | (200,9) | checkpoint1 | 41.261 | 652.6 |
| 2026111200 | (200,9) | checkpoint2 | 49.984 | 585.5 |
| 2026111200 | (200,9) | checkpoint3 | 62.176 | 521.4 |
| 2026111200 | (200,9) | packed_parents | 37.058 | 355.2 |
| 2026111200 | (200,9) | packed_checkpoint2 | 51.631 | 435.0 |
| 2026121200 | (144,5) | parents | 341.622 | 5013.6 |
| 2026121200 | (144,5) | checkpoint1 | 430.564 | 4757.6 |
| 2026121200 | (144,5) | checkpoint2 | 588.857 | 4501.6 |
| 2026121200 | (144,5) | checkpoint3 | 812.901 | 4245.5 |
| 2026121200 | (144,5) | packed_parents | 348.571 | 4245.9 |
| 2026121200 | (144,5) | packed_checkpoint2 | 596.677 | 4253.0 |
| 2026121200 | (200,9) | parents | 37.099 | 481.0 |
| 2026121200 | (200,9) | checkpoint1 | 42.546 | 617.0 |
| 2026121200 | (200,9) | checkpoint2 | 51.402 | 584.1 |
| 2026121200 | (200,9) | checkpoint3 | 63.481 | 486.4 |
| 2026121200 | (200,9) | packed_parents | 38.555 | 354.9 |
| 2026121200 | (200,9) | packed_checkpoint2 | 53.265 | 429.6 |

At (200,9), every retained parent level qualifies for 24-bit storage: link-array bytes fall by exactly 25%. The full policy costs several percent in verified time. Its lower observed allocator reservation also includes explicit cache release, so the entire observed memory difference must not be attributed solely to compression. At (144,5), none of these arrays qualify; all use the 32-bit fallback. Its lower reservation under the named packed policy therefore comes from allocation-release behavior, not truncated indices.

Discarding deeper checkpoints costs additional full reconstruction passes. It is slower in both fixed cohorts and does not reliably lower observed reservation monotonically. On this 16 GB device the ordinary parents path already fits. Retain parents when latency is the priority; use the qualified packed policy for (200,9) only when its memory/time tradeoff is useful. Do not enable blind 24-bit packing or describe deeper checkpoints as a universal improvement.

## Independent nonce outcomes

The two stochastic cohorts compare parents, packed parents and checkpoint1 on 32 disjoint nonces per parameter. All three policies return exactly the same accepted set for every nonce; zero-yield headers are retained.

| Cohort | Parameters | Nonces | Accepted proofs | Zero-yield nonces |
| --- | --- | ---: | ---: | ---: |
| 2026111200 | (144,5) | 32 | 58 | 5 |
| 2026111200 | (200,9) | 32 | 61 | 2 |
| 2026121200 | (144,5) | 32 | 66 | 2 |
| 2026121200 | (200,9) | 32 | 70 | 3 |

These are independent nonces, not repeated fixed-input latency samples. They strengthen the implementation/yield qualification without establishing an ASIC-resistance theorem, deployed mining protocol, network-submission result or economic return.

## Reproduction and evidence

Build [the canonical comparator](build_canonical.py) against the pinned upstream and run [canonical_cpu_study.py](canonical_cpu_study.py) for seeds 2026111200 and 2026121200. Run [checkpoint_study.py](checkpoint_study.py) with default fixed mode and `--stochastic`, repeating with the second seed and distinct output filenames. All executed source/binary bindings, overflow outcomes, rejected repeated-index candidates, zero-yield nonces and returned proofs are retained. `python verify_followups.py` replays every unique retained proof with the independent canonical CPU oracle, checks provenance and produces [followup-summary.csv](results/followup-summary.csv). The original native verifier and altered-proof checks remain part of GPU execution and the existing artifact CI.

GPU campaigns run serially on the same RTX 5060 Ti. Clocks, power limits and unrelated server services are unchanged. No energy or heterogeneous multi-GPU measurement is inferred.
