# Merge Engine Repair — Debugging Task

## Overview

A 3-way merge engine processes branch commit histories from a version control system, computes ancestry depths, generates file-level diffs, detects cross-branch conflicts, resolves them using configurable strategies, and assembles a unified commit graph. The system handles multiple branches with different merge strategies and produces both a merged graph and a conflict resolution report.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, branch data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini

## Architecture

The system processes branch histories through six stages:

1. *Loading* (`/app/runtime/loader.py`) — Reads JSON-format branch files from `/app/runtime/data/`, filtering to only branches whose merge strategy appears in the active_strategies config

2. *Ancestry Tracing* (`/app/runtime/ancestry.py`) — Computes per-commit depth values for each branch. The max_depth in the output represents the longest single branch chain length, not a sum across branches.

3. *Diff Computation* (`/app/runtime/differ.py`) — Collects file modifications per branch and splits the unique file set into fixed-size chunks of chunk_size (from config) for conflict analysis

4. *Conflict Detection* (`/app/runtime/conflict_detector.py`) — Identifies files modified by multiple branches, producing conflict entries sorted by timestamp

5. *Resolution* (`/app/runtime/resolver.py`) — Applies merge strategies using the similarity threshold from the `merge.resolution` configuration section to determine auto-resolve eligibility

6. *Graph Assembly* (`/app/runtime/graph_builder.py`) — Builds the unified commit graph with all commits sorted chronologically. For commits sharing the same timestamp, ordering is deterministic using branch_id alphabetically then seq within that branch.

## Problem

The system produces output but with several anomalies:
- Fewer commits and branches appear than expected given the data files present
- The reported max depth value seems inflated beyond what any single branch should produce
- The similarity threshold used for resolution does not match the intended production configuration
- File diff chunks are larger than the configured chunk size should allow
- Commits at the same timestamp appear in non-deterministic order across runs

## Expected Correct Output

When all defects are resolved:
- All 26 commits from 3 branches (main: 10, feature: 8, hotfix: 8) must be in the graph
- The branch list must include: feature, hotfix, main
- Max depth must be 10 (longest single branch, which is main)
- Similarity threshold must be 60 (from merge.resolution section)
- Chunk count must be 5 (18 unique files / chunk_size 4 = ceil(4.5))
- Commits at timestamp 1700000500 must be ordered: feature, hotfix, main

## Output Schema

### /app/runtime/output/merge_graph.json

| Field | Type | Description |
|-------|------|-------------|
| total_commits | integer | Total commits across all branches |
| branches | array[string] | Sorted list of branch identifiers |
| branch_count | integer | Number of branches in graph |
| commits | array | List of commit objects in order |
| commits[].hash | string | Commit hash identifier |
| commits[].branch_id | string | Source branch for commit |
| commits[].timestamp | integer | Commit timestamp |
| commits[].parent | string | Parent commit hash |
| commits[].message | string | Commit message |
| commits[].depth | integer | Computed ancestry depth |
| commits[].files_touched | integer | Number of files in commit |
| commits[].seq | integer | Sequence within branch |
| max_depth | integer | Maximum depth across all branches |
| conflicts_resolved | integer | Number of file resolutions applied |
| resolved_files | array[string] | Sorted list of resolved filenames |

### /app/runtime/output/conflict_report.json

| Field | Type | Description |
|-------|------|-------------|
| total_conflicts | integer | Total conflict entries detected |
| resolutions | array | List of resolution objects |
| resolution_count | integer | Number of unique file resolutions |
| similarity_threshold | integer | Threshold used for auto-resolution |
| chunk_count | integer | Number of diff chunks produced |
| total_files_analyzed | integer | Unique files across all branches |
| chunks | array | List of chunk objects |
| chunks[].chunk_id | integer | Sequential chunk identifier |
| chunks[].files | array[string] | Files in this chunk |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/config.ini | Merge parameters and strategy configuration |
| /app/runtime/loader.py | Branch data loading with strategy filtering |
| /app/runtime/ancestry.py | Commit depth computation |
| /app/runtime/differ.py | File diff and chunking logic |
| /app/runtime/conflict_detector.py | Cross-branch conflict detection |
| /app/runtime/resolver.py | Conflict resolution with strategy application |
| /app/runtime/graph_builder.py | Unified commit graph assembly |
| /app/runtime/run_merge.py | Main entry point and orchestration |

## Your Task

Identify and fix defects in the runtime source files under `/app/runtime/` so that the system produces correct output matching the expected behavior described above. Multiple modules contain interacting defects that collectively produce incorrect results.
