#!/bin/bash
set -e
python3 /app/runtime/auction_orchestrator.py
python3 /solution/repair_auction_sniper.py
