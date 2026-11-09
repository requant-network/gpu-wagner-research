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
