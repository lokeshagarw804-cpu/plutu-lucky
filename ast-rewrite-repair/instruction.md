# AST Rewriting Compiler — Debugging Task

## Overview

A compiler for a simple expression language parses source programs into AST representations, applies optimization passes (constant folding, dead code elimination, common subexpression elimination), evaluates the optimized ASTs, and produces structured output. The compiler currently produces incorrect results for several test programs.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source, config, data, output)
- *Global system-wide tooling*: uv and pytest are available

## Processing Stages

1. *Parsing* — Converts source text into AST node trees. Supports assignments, arithmetic expressions with standard precedence, variable references, and conditional blocks.

2. *Optimization* — Applies enabled passes to reduce AST complexity: constant folding evaluates compile-time-known operations, dead code elimination removes unused assignments, and CSE replaces duplicate expressions with variable references.

3. *Evaluation* — Executes the optimized AST statements to produce variable bindings. Supports arithmetic, comparisons, and conditional execution.

4. *Emission* — Generates output files with optimized ASTs, evaluation results, and cost summaries.

## Problem

The compiler runs without exceptions but produces wrong evaluation results:
- Arithmetic expressions involving division yield truncated integer values
- Programs using conditional blocks lose variable assignments that should be preserved
- Overall accuracy is below 100% despite the programs being valid

## Expected Correct Output

When functioning correctly:
- All 6 test programs evaluate to their expected results
- Division operations produce floating-point results (7/2 = 3.5)
- Variables referenced inside conditional blocks are preserved by DCE
- Accuracy = 1.0 (6/6 programs correct)

## Output Schema

### /app/runtime/output/evaluation_results.json

| Field | Type | Description |
|-------|------|-------------|
| total_evaluated | int | Number of programs evaluated |
| entries | list | Per-program evaluation results |
| entries[].program_id | string | Program identifier |
| entries[].name | string | Program name |
| entries[].variables | object | Final variable bindings after evaluation |

### /app/runtime/output/optimized_ast.json

| Field | Type | Description |
|-------|------|-------------|
| total_programs | int | Number of programs compiled |
| entries | list | Per-program optimized AST |

### /app/runtime/output/compiler_summary.json

| Field | Type | Description |
|-------|------|-------------|
| total_programs | int | Programs compiled |
| total_statements | int | Statements after optimization |
| total_cost | int | Aggregate execution cost |
| correct_evaluations | int | Programs matching expected results |
| accuracy | float | Fraction of correct evaluations |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/run_compiler.py | Main entry point |
| /app/runtime/parser.py | Expression parser producing AST nodes |
| /app/runtime/optimizer.py | Optimization passes (folding, DCE, CSE) |
| /app/runtime/evaluator.py | AST evaluation engine |
| /app/runtime/emitter.py | Output generation with cost model |
| /app/runtime/config.ini | Compiler configuration |
| /app/runtime/data/programs.json | Test programs with expected results |

## Your Task

Identify and fix defects in the runtime source files under /app/runtime/ that cause incorrect constant folding, improper dead code elimination, and wrong evaluation results.
