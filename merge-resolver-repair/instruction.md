# Merge Resolver Repair — Debugging Task

## Overview

A three-way merge resolution engine analyzes divergent branch edit histories, computes line-level diffs against a common base, classifies conflict hunks using configurable similarity thresholds, scores overlapping regions, and produces a deterministic merge report with conflict annotations. The system handles multiple merge strategies and outputs structured JSON for downstream tooling.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, branch data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini

## Architecture

The system processes branch data through six stages:

1. *Loading* (`/app/runtime/loader.py`) — Reads branch history JSON files from `/app/runtime/data/`

2. *Diffing* (`/app/runtime/differ.py`) — Computes line-level diffs between each branch and the common base, producing hunk records with similarity scores. The strategy for each hunk is read from the edit metadata and validated against the configured strategy list in `/app/runtime/config.ini` under `[strategies]`.

3. *Classification* (`/app/runtime/classifier.py`) — Categorizes hunks as conflicts or auto-resolvable based on the strict conflict threshold. The `[merge.strict]` section in `/app/runtime/config.ini` defines `conflict_threshold=15` for production accuracy. Hunks scoring below this threshold are conflicts.

4. *Scoring* (`/app/runtime/scorer.py`) — Groups hunks into overlapping line regions and computes a single conflict score per region. When multiple hunks cover the same region, the final hunk's severity assessment supersedes earlier ones within that region (last assessment wins).

5. *Resolution* (`/app/runtime/resolver.py`) — Orders conflict entries deterministically for reproducible output. Conflicts at the same line are sorted by `(line_start, branch_id, hunk_id)` to ensure stable ordering since hunk_id is local to each branch.

6. *Reporting* (`/app/runtime/reporter.py`) — Writes merge_report.json and region_summary.json to `/app/runtime/output/`

## Problem

The system runs without errors but produces incorrect results:
- Some hunks that should use the "minimal" strategy fall back to the default strategy
- The conflict/auto-resolved classification counts appear wrong — too many hunks marked as conflicts
- Region-level conflict scores seem inflated compared to expected values
- The ordering of conflicts at the same line number is inconsistent across different environments

## Expected Correct Output

When all defects are resolved:
- The system should recognize all 4 configured merge strategies: recursive, patience, histogram, minimal
- With strict threshold classification, exactly 6 hunks should be conflicts and 4 should be auto-resolved
- Region scores should reflect final hunk severity (not accumulated), with values around 80-88
- Conflicts at the same line should be ordered by branch_id then hunk_id for deterministic output

## Output Schema

### /app/runtime/output/merge_report.json

| Field | Type | Description |
|-------|------|-------------|
| total_conflicts | integer | Number of conflict hunks |
| total_auto_resolved | integer | Number of auto-resolved hunks |
| strategies_used | array[string] | Sorted list of strategies encountered |
| branch_count | integer | Number of branches loaded |
| conflicts | array | Ordered list of conflict entries |
| conflicts[].line_start | integer | First line of conflict |
| conflicts[].line_end | integer | Last line of conflict |
| conflicts[].branch_id | string | Branch containing the conflict |
| conflicts[].hunk_id | integer | Hunk identifier within the branch |
| conflicts[].severity | integer | Conflict severity (100 minus similarity) |
| conflicts[].strategy | string | Merge strategy used for this hunk |
| conflicts[].content_preview | string | First 80 chars of hunk content |

### /app/runtime/output/region_summary.json

| Field | Type | Description |
|-------|------|-------------|
| total_regions | integer | Total number of line regions |
| conflicting_regions | integer | Regions containing at least one conflict |
| clean_regions | integer | Regions with no conflicts |
| regions | array | List of scored region objects |
| regions[].line_start | integer | First line of region |
| regions[].line_end | integer | Last line of region |
| regions[].hunk_count | integer | Hunks in this region |
| regions[].conflict_score | integer | Region conflict severity score |
| regions[].has_conflict | boolean | Whether region has any conflict hunks |
| regions[].branches | array[string] | Branches contributing to this region |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/config.ini | Merge parameters, strategy list, thresholds |
| /app/runtime/loader.py | Branch data loading |
| /app/runtime/differ.py | Line-level diff computation with strategy validation |
| /app/runtime/classifier.py | Conflict threshold classification |
| /app/runtime/scorer.py | Region-level conflict scoring |
| /app/runtime/resolver.py | Deterministic conflict ordering |
| /app/runtime/reporter.py | JSON report generation |
| /app/runtime/run_merge.py | Main entry point |

## Your Task

Identify and fix defects in the runtime source files under `/app/runtime/` so that the merge resolution engine produces correct output matching the expected behavior described above. Multiple modules contain interacting defects that collectively produce incorrect results.
