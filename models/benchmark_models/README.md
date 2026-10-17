# Benchmark Model Checkpoints Manifest

**Project**: SIH 2026 Problem Statement 26168 — Intelligent Dead Reckoning (IDR) System  
**Repository**: `https://github.com/Yugenjr/SIH-2026-1.git`  
**Purpose**: Catalog and organize byte-for-byte verified model checkpoints corresponding to reported M028 and M029 benchmark evaluations.

---

## Benchmark Checkpoint Inventory

| Milestone | Checkpoint Filename | Original Repository Path | Type | SHA-256 Hash | Reported Benchmark Result |
|---|---|---|---|---|---|
| **M028** | `M028_baseline_speednet_v2_w40.pth` | [`models/speednet_v2_w40.pth`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/models/speednet_v2_w40.pth) | Neural Network Checkpoint (SpeedNet v2, W=40) | `2b467d8198d3f4d9e6ac2b0e6641e8b5ac7cb51778ec25ba96198a3f5b75a681` | **218.93 m @ 300 s outage** |
| **M029** | `M029_heading_anchor_speednet_v2_w40.pth` | [`models/speednet_v2_w40.pth`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/models/speednet_v2_w40.pth) | Neural Network Checkpoint (SpeedNet v2, W=40) | `2b467d8198d3f4d9e6ac2b0e6641e8b5ac7cb51778ec25ba96198a3f5b75a681` | **48.20 m @ 300 s outage** |

---

## Checkpoint & Architecture Mapping Note

- **Identical Neural Checkpoint**: Both M028 and M029 benchmarks utilize the **exact same PyTorch neural-network model checkpoint** ([`models/speednet_v2_w40.pth`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/models/speednet_v2_w40.pth)).
- **Source of M029 Improvement**: The 300-second position error reduction from **218.93 m (M028)** down to **48.20 m (M029)** is achieved entirely through the **Multi-Anchor Heading Architecture** (SpeedNet yaw-rate fusion + motion-gated zero-yaw constraint + causal pre-outage GNSS course latching + 6-state heading manager) without retraining or modifying the underlying neural network weights.
- **Byte-for-Byte Verification**: Both copies (`M028_baseline_speednet_v2_w40.pth` and `M029_heading_anchor_speednet_v2_w40.pth`) are byte-for-byte identical to the original checkpoint file `models/speednet_v2_w40.pth` (Size: 370,686 bytes).

---

## Verification Statement

All benchmark copies in [`models/benchmark_models/`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/models/benchmark_models) are unchanged copies of the original verified checkpoints. No model weights, architectural layers, or inference parameters have been modified.
