# Three-Way Merge Engine — Debugging Task

## Overview

A three-way merge engine takes a base document version along with two branch modifications, computes line-level differences, detects conflicting changes, resolves conflicts using precedence rules, and assembles a final merged document. The engine currently produces incorrect merge results with too many false conflicts and missing content in the output.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source, config, data, output)
- *Global system-wide tooling*: uv and pytest are available

## Processing Stages

1. *Diff Computation* — For each section, computes change regions between the base and each branch. A change region records the start and end line indices (inclusive), the original lines, and the replacement lines. Region types are "modify", "add", or "delete".

2. *Conflict Detection* — Identifies pairs of change regions (one from each branch) that constitute a true merge conflict. A conflict occurs when two regions overlap in their line range AND neither is a pure addition. Non-conflapping or addition-only changes are classified as auto-resolvable.

3. *Conflict Resolution* — Applies resolution strategy to each detected conflict pair. With "branch_a_first" precedence, branch A's lines are selected at odd resolution depths. The resolver processes conflicts iteratively with a shared context.

4. *Document Assembly* — Reconstructs the merged section by applying resolutions and auto-resolved changes to the base lines. Changes are applied in reverse position order to maintain correct indices. Line ranges use inclusive boundaries throughout the system.

5. *Output Generation* — Writes the merged document, conflict report, and processing summary.

## Problem

The merge engine runs without errors but produces incorrect output:
- Far too many conflicts are reported (non-overlapping changes incorrectly classified)
- Auto-resolved change count is zero when it should be significant
- Merged sections are shorter than expected (lines being lost during assembly)
- Some conflict resolutions appear to be using wrong branch selection

## Expected Correct Output

When functioning correctly:
- Only 2 true conflicts detected (in sections S01 and S02 where branches modify overlapping lines)
- 18 changes auto-resolved without conflict
- Merged section line counts: S01=6, S02=6, S03=7, S04=7, S05=7 (total 33 lines)
- Additions from both branches appear in non-conflicting sections

## Output Schema

### /app/runtime/output/merged_document.json

| Field | Type | Description |
|-------|------|-------------|
| doc_id | string | Document identifier |
| version | string | Always "merged" |
| sections | list | Merged section entries |
| sections[].id | string | Section identifier |
| sections[].title | string | Section title |
| sections[].lines | list | Final merged line content |

### /app/runtime/output/conflict_report.json

| Field | Type | Description |
|-------|------|-------------|
| total_conflicts | int | Number of true conflicts detected |
| total_auto_resolved | int | Non-conflicting changes auto-resolved |
| conflict_details | list | Per-conflict detail records |

### /app/runtime/output/merge_summary.json

| Field | Type | Description |
|-------|------|-------------|
| sections_processed | int | Number of document sections merged |
| total_conflicts | int | Conflicts detected |
| total_auto_resolved | int | Auto-resolved changes |
| merged_section_line_counts | object | Line count per section after merge |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/run_merge.py | Main entry point orchestrating the merge |
| /app/runtime/diff_engine.py | Line-level diff computation with ChangeRegion class |
| /app/runtime/conflict_detector.py | Identifies overlapping conflicting regions |
| /app/runtime/resolver.py | Applies resolution strategy to conflict pairs |
| /app/runtime/assembler.py | Reconstructs merged document from resolved changes |
| /app/runtime/config.ini | Merge and resolution configuration |
| /app/runtime/data/document_base.json | Base version of the document |
| /app/runtime/data/document_branch_a.json | Branch A modifications |
| /app/runtime/data/document_branch_b.json | Branch B modifications |

## Your Task

Identify and fix the defects in the runtime source files under /app/runtime/ that cause incorrect conflict detection, lost content in assembly, and wrong resolution selections.
