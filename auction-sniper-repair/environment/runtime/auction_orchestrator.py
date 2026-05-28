"""
Auction sniper simulation orchestrator.

This is the main entry point that coordinates the full simulation pipeline:
  1. Parse the auction log into structured events
  2. Initialize and run the bid tracker to compute activity vectors
  3. Generate the strategy evaluation report

Usage:
    python3 /app/runtime/auction_orchestrator.py

Outputs:
    /app/runtime/bid_state.jsonl  — per-event state records
    /app/runtime/strategy_report.json — final classification report
"""

import sys
import os

# Ensure runtime directory is on the path
RUNTIME_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RUNTIME_DIR)

from event_parser import load_auction_log, extract_bot_ids
from bid_tracker import BidTracker
from auction_report import generate_strategy_report


# ═══════════════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════════════

AUCTION_LOG_PATH = os.path.join(RUNTIME_DIR, 'auction_log.dat')
STATE_OUTPUT_PATH = os.path.join(RUNTIME_DIR, 'bid_state.jsonl')
REPORT_OUTPUT_PATH = os.path.join(RUNTIME_DIR, 'strategy_report.json')


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    """Execute the full auction sniper simulation pipeline."""
    
    # Stage 1: Parse auction log
    print("[1/3] Parsing auction log...")
    events = load_auction_log(AUCTION_LOG_PATH)
    bot_ids = extract_bot_ids(events)
    print(f"      Loaded {len(events)} events for {len(bot_ids)} bots")
    print(f"      Bots: {', '.join(bot_ids)}")
    
    # Stage 2: Run bid tracker
    print("[2/3] Running bid tracker...")
    tracker = BidTracker(bot_ids, STATE_OUTPUT_PATH)
    tracker.process_all_events(events)
    final_vectors = tracker.get_final_vectors()
    print(f"      State file written: {STATE_OUTPUT_PATH}")
    print(f"      Final vectors computed for {len(final_vectors)} bots")
    
    # Stage 3: Generate strategy report
    print("[3/3] Generating strategy report...")
    report = generate_strategy_report(
        bot_ids, final_vectors, events, REPORT_OUTPUT_PATH
    )
    print(f"      Report written: {REPORT_OUTPUT_PATH}")
    print(f"      Independent pairs: {report['independence_analysis']['independent_pair_count']}")
    print(f"      Execution order: {report['execution_plan']['order']}")
    print(f"      Integrity digest: {report['integrity']['digest']}")
    
    print("\n[DONE] Auction sniper simulation complete.")
    return report


if __name__ == '__main__':
    main()
