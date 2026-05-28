#!/bin/bash
set -e
python3 /app/runtime/orchestrator.py
python3 /solution/repair_packet_flow.py
