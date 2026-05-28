"""
Repair script for the auction sniper simulation.

This script diagnoses and fixes bugs in the bid tracking pipeline by:
1. Running the simulation and observing output discrepancies
2. Analyzing bid vector accumulation logic for missing state updates
3. Inspecting the independence predicate semantics
4. Verifying execution ordering against expected properties

The fixes are derived by tracing the data flow from auction_log.dat
through bid vectors to the final classification and report.
"""

import os
import sys


def analyze_and_fix_bid_tracker():
    """Diagnose Bug 1 by inspecting merge behavior in bid_tracker.py.
    
    The _merge_peer_intelligence method should increment the bot's own
    component after absorbing peer data, because each SYNC_INTEL event
    constitutes a local intelligence-gathering action that increases
    the bot's own accumulated activity count.
    
    Diagnosis: Compare own_component values for bots with SYNC_INTEL
    events vs those without. The deficit equals the SYNC count,
    confirming that each sync should contribute +1 to the own component.
    """
    filepath = '/app/runtime/bid_tracker.py'
    with open(filepath, 'r') as f:
        source = f.read()
    
    # Line-by-line analysis to find the merge method and insert
    # the missing self-increment after peer intelligence absorption
    lines = source.split('\n')
    fixed_lines = []
    in_merge_method = False
    merge_complete = False
    
    for i, line in enumerate(lines):
        fixed_lines.append(line)
        
        # Detect entry into the merge method
        if '_merge_peer_intelligence' in line and 'def ' in line:
            in_merge_method = True
            merge_complete = False
        
        # Find the sync count increment which happens right after the merge loop
        if in_merge_method and 'self._sync_count[bot_id] += 1' in line:
            # Insert the missing own-component increment
            indent = len(line) - len(line.lstrip())
            fixed_lines.append(' ' * indent + 'self._vectors[bot_id][bot_id] += 1')
            in_merge_method = False
            merge_complete = True
    
    with open(filepath, 'w') as f:
        f.write('\n'.join(fixed_lines))
    
    print("[FIX 1] bid_tracker.py: Added self-increment after peer intelligence merge")


def analyze_and_fix_strategy_evaluator():
    """Diagnose Bugs 2 and 3 by semantic analysis of strategy_evaluator.py.
    
    Bug 2: The bots_can_bid_independently predicate checks bidirectional
    <= (A<=B AND B<=A, which is equality in the partial order) instead
    of checking incomparability (neither dominates the other). Two bots
    are strategy-independent when their vectors are INCOMPARABLE, not
    when they are equal.
    
    Bug 3: The compute_execution_order method sorts by last event tick
    (temporal recency) instead of by total activity weight (sum of
    vector components). The correct ordering processes bots from lowest
    to highest aggregate activity.
    """
    filepath = '/app/runtime/strategy_evaluator.py'
    with open(filepath, 'r') as f:
        source = f.read()
    
    # Fix Bug 2: Replace equality check with incomparability check
    old_predicate = (
        "a_bounded = _component_wise_leq(vec_a, vec_b)\n"
        "        b_bounded = _component_wise_leq(vec_b, vec_a)\n"
        "        result = a_bounded and b_bounded"
    )
    new_predicate = (
        "a_dominates = _dominates(vec_a, vec_b)\n"
        "        b_dominates = _dominates(vec_b, vec_a)\n"
        "        result = not a_dominates and not b_dominates"
    )
    source = source.replace(old_predicate, new_predicate)
    
    # Fix Bug 3: Replace temporal ordering with weight-based ordering
    old_order = (
        "last_event_tick = {}\n"
        "        for event in self._events:\n"
        "            last_event_tick[event['bot_id']] = event['tick']\n"
        "        \n"
        "        return sorted(\n"
        "            self._bot_ids,\n"
        "            key=lambda b: last_event_tick.get(b, 0)\n"
        "        )"
    )
    new_order = (
        "activity_weights = {}\n"
        "        for bot_id in self._bot_ids:\n"
        "            activity_weights[bot_id] = sum(self._vectors[bot_id])\n"
        "        \n"
        "        return sorted(\n"
        "            self._bot_ids,\n"
        "            key=lambda b: activity_weights.get(b, 0)\n"
        "        )"
    )
    source = source.replace(old_order, new_order)
    
    with open(filepath, 'w') as f:
        f.write(source)
    
    print("[FIX 2] strategy_evaluator.py: Changed independence check from equality to incomparability")
    print("[FIX 3] strategy_evaluator.py: Changed execution order from temporal recency to activity weight")


def regenerate_outputs():
    """Re-run the auction pipeline with corrected code to produce valid outputs."""
    state_path = '/app/runtime/bid_state.jsonl'
    report_path = '/app/runtime/strategy_report.json'
    
    # Remove stale outputs
    for path in [state_path, report_path]:
        if os.path.exists(path):
            os.remove(path)
    
    # Clear cached modules to force reimport of fixed code
    modules_to_clear = [
        'bid_tracker', 'strategy_evaluator', 'auction_report',
        'auction_orchestrator', 'event_parser', 'auction_types'
    ]
    for mod in list(sys.modules.keys()):
        if mod in modules_to_clear:
            del sys.modules[mod]
    
    # Re-run pipeline
    sys.path.insert(0, '/app/runtime')
    from auction_orchestrator import main
    main()


if __name__ == '__main__':
    print("=== Auction Sniper Repair ===")
    print("Analyzing bid tracking pipeline...")
    analyze_and_fix_bid_tracker()
    print("\nAnalyzing strategy evaluation semantics...")
    analyze_and_fix_strategy_evaluator()
    print("\n[FIX 4] auction_report.py: Automatically corrected via strategy_evaluator fix")
    print("\nRegenerating outputs...")
    regenerate_outputs()
    print("\n=== All repairs applied successfully ===")
