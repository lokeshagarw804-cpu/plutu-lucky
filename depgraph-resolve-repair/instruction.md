# Dependency Graph Resolution — Debugging Task

## Overview

A package dependency resolution system loads package registry data, filters by scope, recursively resolves version constraints, computes a deterministic installation order, and generates an integrity-checksummed manifest. The system currently produces incorrect resolution results across multiple dimensions.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source, config, data, output)
- *Global system-wide tooling*: uv and pytest are available

## Processing Stages

1. *Loading* — Reads package definitions from registry JSON files in /app/runtime/data/. Each file contains packages with versions, dependency constraints, and scope designations.

2. *Scope Filtering* — Removes packages whose scope appears in the exclusion list. The exclusion configuration controls which dependency scopes are stripped before resolution begins.

3. *Resolution* — Starting from configured root packages, recursively resolves dependencies by matching version constraints. The strategy selects the highest compatible version meeting each constraint. Resolution depth is bounded by strict parameters for production builds.

4. *Graph Construction* — Builds the directed dependency graph and computes installation order. Leaf packages (deepest in the tree) are installed before their dependents to satisfy build requirements.

5. *Manifest Writing* — Produces the resolution manifest with installation positions, dependency graph structure, and an integrity checksum. The checksum covers only the fields specified in configuration to remain stable across metadata changes.

## Problem

The system runs without exceptions but produces a manifest that fails integrity verification:
- The total package count differs from expected
- Version selections do not satisfy declared constraints
- Installation ordering violates the leaves-first requirement
- The integrity checksum does not match expected value

## Expected Correct Output

When functioning correctly:
- Exactly 15 packages are resolved (all runtime scope)
- No peer or dev scoped packages appear in the resolution
- The highest compatible version is selected for each constraint
- Maximum resolution depth does not exceed the strict limit
- Installation order places leaf dependencies before their dependents
- The integrity checksum matches the deterministic expected value

## Output Schema

### /app/runtime/output/resolution_manifest.json

| Field | Type | Description |
|-------|------|-------------|
| total_packages | int | Number of resolved packages |
| entries | list | Ordered list of resolved package entries |
| entries[].package | string | Package name |
| entries[].version | string | Selected version |
| entries[].scope | string | Package scope |
| entries[].depth | int | Depth in dependency tree |
| entries[].install_position | int | Position in installation sequence |
| integrity_checksum | string | SHA256-based integrity hash (16 hex chars) |

### /app/runtime/output/dependency_graph.json

| Field | Type | Description |
|-------|------|-------------|
| nodes | object | Graph nodes keyed by package name |
| node_count | int | Total nodes in the graph |

### /app/runtime/output/resolve_summary.json

| Field | Type | Description |
|-------|------|-------------|
| total_resolved | int | Total packages resolved |
| by_scope | object | Count of packages per scope |
| by_depth | object | Count of packages per depth level |
| max_depth_reached | int | Maximum depth encountered |
| graph_nodes | int | Number of graph nodes |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/run_resolve.py | Main entry point |
| /app/runtime/loader.py | Registry data loading |
| /app/runtime/scope_filter.py | Scope-based package filtering |
| /app/runtime/resolver.py | Recursive dependency resolution |
| /app/runtime/graph_builder.py | Graph construction and install ordering |
| /app/runtime/manifest_writer.py | Output file generation and checksumming |
| /app/runtime/config.ini | Resolution configuration |
| /app/runtime/data/registry_core.json | Core framework packages |
| /app/runtime/data/registry_plugins.json | Plugin packages |
| /app/runtime/data/registry_tooling.json | Development and peer tooling packages |

## Your Task

Identify and fix the defects in the runtime source files under /app/runtime/ that cause incorrect scope filtering, wrong version selection, improper installation ordering, and checksum mismatch.
