# Cache Eviction Repair — Debugging Task

## What this is

Multi-tier caching system. Reads access requests from three client streams, manages L1/L2 cache tiers with LRU eviction, handles promotion between tiers, and generates performance reports.

## Environment

- Python 3.11, working dir `/app`, source `/app/runtime/`, output `/app/runtime/output/`
- pytest available globally

## Processing stages

1. **Load** — Read access request streams from each client.
2. **Cache** — Process requests through two-tier cache with eviction policy.
3. **Promote** — Move frequently-accessed L2 entries to L1 based on configured thresholds.
4. **Report** — Compute hit/miss ratios and cache utilization metrics.

## Symptoms

Cache hit rates much lower than expected. LRU eviction seems to remove wrong entries. Promotion between tiers happens less often than it should. Per-client statistics don't add up correctly in the aggregate.

## Expected output

- `/app/runtime/output/cache_stats.json`: list with `client`(str), `l1_hits`(int), `l2_hits`(int), `misses`(int), `promotions`(int)
- `/app/runtime/output/summary.json`: `total_requests`, `overall_hit_rate`, `l1_hit_rate`, `promotions_total`, `evictions_total`

## Key files

| File | Purpose |
|------|---------|
| `/app/runtime/eviction.py` | LRU cache with eviction logic |
| `/app/runtime/promoter.py` | L2→L1 tier promotion |
| `/app/runtime/reporter.py` | Performance statistics |
| `/app/runtime/config.ini` | Cache sizes, thresholds |

## Task

Find and fix the bugs. Multiple interacting defects across files.
