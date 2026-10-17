# M041 SIH Benchmark Compliance Audit Summary

## Executive Summary
- **Primary Goal:** Audit current production locked pipeline (M028/M040) against the SIH requirement: **Final Position Drift < 10% of Reference Distance Travelled** (<100 m / km).
- **Audit Verdict:**
  - **60 s Outage:** **PASS** (FPER = 6.82%, Error/km = 68.18 m/km < 100 m/km)
  - **120 s Outage:** **FAIL** (FPER = 48.72%, Error/km = 487.18 m/km > 100 m/km)
  - **300 s Outage:** **FAIL** (FPER = 15.81%, Error/km = 158.11 m/km > 100 m/km)
  - **1 km Travel Benchmark:** **FAIL** (FPER at 1 km = 30.74%, Error at 1 km = 307.46 m)

## Benchmark Compliance Table

| Outage Duration | Reference Distance ($D_{ref}$) | Production Error | SIH Allowable Limit (10%) | FPER (%) | Error / km | SIH Status |
|-----------------|----------------------------------|------------------|---------------------------|----------|------------|------------|
| **60 s** | 409.0 m | 27.88 m | 40.9 m | **6.82%** | **68.18 m/km** | <span style="color:green; font-weight:bold;">PASS</span> |
| **120 s** | 874.76 m | 426.17 m | 87.48 m | **48.72%** | **487.18 m/km** | <span style="color:red; font-weight:bold;">FAIL</span> |
| **300 s** | 1384.63 m | 218.93 m | 138.46 m | **15.81%** | **158.11 m/km** | <span style="color:red; font-weight:bold;">FAIL</span> |

## 1 km Distance-Normalized Benchmark Table

| Metric | Current Production Pipeline | SIH Problem Limit | Compliance Status |
|--------|-----------------------------|-------------------|-------------------|
| **1 km Reference Distance Reached?** | **YES** (1000.17 m) | N/A | Exceeded |
| **Elapsed Outage Time ($T_{1km}$)** | **150.0 s** | N/A | Measured |
| **Final Position Error at 1 km** | **307.46 m** | < 100.00 m | <span style="color:red; font-weight:bold;">FAIL</span> |
| **Final Position Error Ratio (FPER)** | **30.74%** | < 10.00 % | <span style="color:red; font-weight:bold;">FAIL</span> |
| **Error per Kilometre** | **307.41 m/km** | < 100.00 m/km | <span style="color:red; font-weight:bold;">FAIL</span> |

## Practical SIH Operating Envelope
- **Maximum Compliant Travel Distance ($D_{max}$):** **49.78 m** (~0.49 km)
- **Maximum Compliant Outage Time ($T_{max}$):** **5.1 s**
