#!/bin/bash
set -e
python3 /app/runtime/simulator.py
python3 /solution/repair_collision.py
