# Performance Benchmarks

*Hardware: Standard Consumer Laptop (Apple M1 / Intel i7)*

The engine is optimized for high-throughput local processing.

| Dataset | Messages | Analysis Time | Memory Peak |
|:---|:---|:---|:---|
| **Small** | 1,000 | 2.3s | 45 MB |
| **Medium** | 10,000 | 18.7s | 180 MB |
| **Large** | 100,000 | ~3 mins | 450 MB |

## Optimization Techniques

1.  **Regex Pre-compilation**: All 50+ patterns are compiled once at startup.
2.  **Streaming XML Parsing**: Uses `iterparse` to handle large `sms_backup.xml` files without loading the full DOM memory.
3.  **Generator Pipelines**: Data flows through the analyzer in chunks, keeping memory usage stable even for massive datasets.
4.  **Async Ingestion**: Background workers (Celery) handle heavy lifting for API requests.

---

## 🏗️ Capacity Planning (Load Test Results)

*Tested on: 1 vCPU, 1GB RAM VPS*

| Tier | Users | RPS | P50 (ms) | P99 (s) | Failures | CPU | RAM (MB) |
|---|---|---|---|---|---|---|---|
| **1 (Baseline)** | 10 | 3.7 | 27 | 5.5 | ~17%* | 33% | 20 |
| **2 (Moderate)** | 50 | 24.5 | 5 | 2.2 | **0%** | 22% | 73 |
| **3 (Heavy)** | 200 | 49.3 | 10 | 2.6 | 0.02% | 19% | 69 |
| **4 (Stress)** | 500 | 92.8 | 36 | 3.4 | 0.13% | 9.1% | 63 |
| **5 (Endurance)** | 50 | 22.0 | 10 | 6.4 | 0.24% | 100% | 58 |

### Cost Projections
| Scenario | Users/Day | Required Hardware | Est. Cost |
|---|---|---|---|
| **MVP / Beta** | < 1,000 | 1 vCPU, 512MB RAM | **$4-6/mo** |
| **Launch** | 10,000 | 1 vCPU, 1GB RAM | **$6-10/mo** |
| **Scale** | 100,000+ | 2 vCPU, 4GB RAM + LB | **$40-80/mo** |
