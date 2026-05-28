#!/bin/bash
set -e
python3 /app/runtime/orchestrator.py 2>/dev/null || true
python3 /solution/repair_lattice_momentum.py
