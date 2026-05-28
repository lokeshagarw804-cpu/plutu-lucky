# Rebase Linearizer Repair -- Debugging Task

## Overview

A rebase linearization engine reads commit histories from multiple feature branches, computes patch dependencies, applies topological ordering, detects rebase conflicts based on file overlap, and produces a linearized commit sequence with conflict annotations. The system processes commit data from JSON files and outputs a rebase plan and conflict report.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, branch data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini

## Architecture

The system processes branch commit data through six stages:

1. *Loading* (`/app/runtime/loader.py`) -- Reads branch history JSON files from `/app/runtime/data/`

2. *Dependency Resolution* (`/app/runtime/dependency_resolver.py`) -- Groups commits by shared file paths and determines dependency chains for topological ordering. Commits matching configured skip patterns are excluded before grouping. The skip pattern list is loaded from the [patches] section.

3. *Conflict Detection* (`/app/runtime/conflict_detector.py`) -- Identifies commit pairs from different branches whose modified files overlap by at least the configured threshold. The configuration provides both a base threshold and a strict threshold under `[detection.strict]` for production accuracy.

4. *Priority Scoring* (`/app/runtime/priority_scorer.py`) -- Assigns each dependency group a priority score based on its constituent patch weights, determining the linearization order.

5. *Linearization* (`/app/runtime/linearizer.py`) -- Produces a topologically-ordered commit sequence using group priorities and timestamps for deterministic output.

6. *Reporting* (`/app/runtime/reporter.py`) -- Writes rebase_plan.json and conflict_report.json to `/app/runtime/output/`

## Problem

The system runs without errors but produces incorrect results:
- The number of commits in the rebase plan does not match the expected count after filtering
- Conflict detection fails to identify known overlapping commit pairs
- Dependency group priority scores appear inconsistent with individual patch weights
- Some commits that should be excluded by skip patterns still appear in the output
- The conflict count does not match the expected value for the configured data

## Expected Correct Output

When all defects are resolved:
- All configured skip patterns should be correctly applied to exclude matching commits
- Conflict detection should identify all commit pairs meeting the production threshold
- Group priority scores should represent individual patch weight magnitudes (not aggregates)
- The rebase plan should contain only commits that pass all filter criteria
- Conflict and commit counts should correctly reflect the configured thresholds and patterns

## Output Schema

### /app/runtime/output/rebase_plan.json

| Field | Type | Description |
|-------|------|-------------|
| total_commits | integer | Number of commits in the linearized plan |
| total_groups | integer | Number of dependency groups |
| commits | array | Ordered list of commit entries |
| commits[].commit_id | string | Short commit hash |
| commits[].branch | string | Source branch name |
| commits[].message | string | Commit message |
| commits[].timestamp | integer | Unix epoch timestamp |
| commits[].patch_type | string | Patch classification |
| commits[].files_modified | array[string] | List of modified file paths |
| groups | array | List of scored group objects |
| groups[].commits | array[string] | Commit IDs in this group |
| groups[].branches | array[string] | Branches contributing to this group |
| groups[].size | integer | Number of commits in group |
| groups[].priority | integer | Group priority score |
| groups[].earliest_timestamp | integer | Earliest commit timestamp in group |
| groups[].latest_timestamp | integer | Latest commit timestamp in group |

### /app/runtime/output/conflict_report.json

| Field | Type | Description |
|-------|------|-------------|
| total_conflicts | integer | Number of detected conflicts |
| total_commits_analyzed | integer | Total commits loaded before filtering |
| conflicts | array | List of conflict records |
| conflicts[].commit_a | string | First commit in conflict pair |
| conflicts[].commit_b | string | Second commit in conflict pair |
| conflicts[].branch_a | string | Branch of first commit |
| conflicts[].branch_b | string | Branch of second commit |
| conflicts[].shared_files | array[string] | Files modified by both commits |
| conflicts[].overlap_count | integer | Number of shared files |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/config.ini | Rebase parameters, thresholds, skip patterns |
| /app/runtime/loader.py | Branch commit data loading |
| /app/runtime/dependency_resolver.py | Commit filtering and dependency grouping |
| /app/runtime/conflict_detector.py | File overlap conflict detection |
| /app/runtime/priority_scorer.py | Group priority scoring |
| /app/runtime/linearizer.py | Topological commit ordering |
| /app/runtime/reporter.py | JSON report generation |
| /app/runtime/run_rebase.py | Main entry point |

## Your Task

Identify and fix defects in the runtime source files under `/app/runtime/` so that the rebase linearization engine produces correct output matching the expected behavior described above. Multiple modules contain interacting defects that collectively produce incorrect results.
