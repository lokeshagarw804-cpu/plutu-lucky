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

2. *Diffing* (`/app/runtime/differ.py`) — Computes line-level diffs between each branch and the common base, producing hunk records with similarity scores. Each hunk carries a strategy annotation from the edit metadata, validated against the configured strategy list.

3. *Classification* (`/app/runtime/classifier.py`) — Categorizes hunks as conflicts or auto-resolvable using the conflict threshold. The configuration provides both a base threshold (used during development) and a strict threshold under `[merge.strict]` for production accuracy. Hunks scoring below the active threshold are conflicts; those at or above are auto-resolved.

4. *Scoring* (`/app/runtime/scorer.py`) — Groups hunks into overlapping line regions and computes a single conflict score per region representing severity.

5. *Resolution* (`/app/runtime/resolver.py`) — Orders conflict entries deterministically for reproducible output across environments.

6. *Reporting* (`/app/runtime/reporter.py`) — Writes merge_report.json and region_summary.json to `/app/runtime/output/`

## Problem

The system runs without errors but produces incorrect results:
- The number of recognized merge strategies does not match the configured count
- Conflict classification counts differ from expected values for the given data
- Region-level conflict scores appear inconsistent with individual hunk severities
- The ordering of conflicts sharing a line number varies between runs on different platforms
- Some hunks from a specific branch fail to appear in the conflict report despite low similarity

## Expected Correct Output

When all defects are resolved:
- All configured merge strategies should be recognized and appear in the output
- Conflict and auto-resolved counts should correctly reflect the threshold classification
- Region scores should represent single-hunk severity magnitudes (not multi-hunk aggregates)
- Conflict ordering must be fully deterministic regardless of platform or run order
- All qualifying hunks from both branches must appear in the final conflict list

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
