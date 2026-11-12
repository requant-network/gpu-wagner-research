# Research protocol

A research project by [Requant Network](https://requant.network).

## Required experiments

1. Reproduce the pinned TCHES 2026 C++ artifact on this CPU, including solution verification, independent seeds and measured time/memory. Distinguish the artifact hash convention from a network-compatible Equihash instance.
2. Implement independent small-instance single-list and regular multi-list CPU references, exhaustive checks, canonical collision-tree validation and altered-solution rejection.
3. Execute a complete GPU single-list solver with exact pair counting and no silent bucket truncation. Compare explicit index vectors, parent pointers and checkpoint/recomputation, including reconstruction and verification.
4. Scale to canonical Equihash parameters that fit the 16 GB device, with independent BLAKE2b leaf checks and an upstream verifier. Measure complete time, allocation peaks and accepted solutions; characterize solution losses explicitly.
5. Compare regular-list and single-list behavior with matched documented workloads. Do not label a scaled regular GBP experiment as a full deployed Requihash miner.

## Shared evidence requirements

Use the released RTX 5060 Ti 16 GB without concurrent GPU experiments. Retain exact executed-source hashes, pinned upstream revisions, environment, raw measurements, independent correctness evidence, timing boundaries and reproduction commands. Fixed-input latency comparisons use five warm-ups and thirty measured repetitions where practical. Stochastic search uses independent seeds and retains unsuccessful/censored trials. Energy requires sampled measurements; no TDP-derived efficiency claims.

## Completion requirements

Publish executable CPU/GPU studies, all required comparisons, independent verification, raw results, derived tables, English final conclusions and limitations. Public repository topics, homepage and attribution must identify Requant Network. CPU/reference and artifact CI must pass at the published commit. A negative result may complete a hypothesis test; missing experiments may not.

## Completion evidence

| Requirement | Evidence |
| --- | --- |
| Pinned native artifact and independent time/memory/proof checks | `build_native.py`, `author_campaign.py`, both complete author records; hash convention and duplicate candidates disclosed. |
| Independent small references and altered-proof rejection | `experiments/birthday.py`, `cpu_study.py`, retained proof replay and exhaustive tiny fixture. |
| Exact GPU solver and all memory policies | `cuda/wagner.cu`, `gpu_study.py`, complete primary/disjoint replication and fixed-input studies. |
| Canonical full parameters, hash/verifier checks and explicit losses | (144,5)/(200,9) proofs, hashlib samples, Tromp validation, candidate/rejection counts and allocator follow-up. |
| Matched regular/single workloads | `regular_study.py`, two cohorts with complete CPU/GPU solution sets on identical initial leaves/counts. |

The [final report](FINAL_REPORT.md) and derived tables document findings, negative
outcomes, reproduction and limits. The earlier overlapping canonical cohort is
retained as a repeat control and supplemented by a disjoint independent cohort.
This bounded campaign is complete; a deployed miner and energy economics remain
separate work.

## Follow-up closure, 12 November 2026

The [follow-up report](FOLLOWUP_REPORT.md) records the disposition of the concrete next steps: new experiments, negative findings and measured resource limits. The earlier completed campaign remains available for historical comparison. Run `python verify_followups.py` for the added evidence checks.
