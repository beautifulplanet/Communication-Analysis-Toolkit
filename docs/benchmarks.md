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
