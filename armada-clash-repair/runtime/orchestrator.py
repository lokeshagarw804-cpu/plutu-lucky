"""Orchestrator for armada clash simulation.

Coordinates the full engagement processing pipeline from raw event
ingestion through vector computation to final report generation.
"""
import json
import os

from runtime.parser import parse_engagements
from runtime.vector_engine import VectorClock, FLEET_COUNT, BASE_VALUE
from runtime.clash_analyzer import fleets_are_autonomous, compute_deployment_priority
from runtime.armada_report import build_report
from runtime.fleet_doctrine import DoctrineProfile, FleetFormation


def run_simulation():
    """Execute the complete armada clash simulation pipeline."""
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Load engagement events
    events = parse_engagements()

    # Initialize vector clocks for all armadas
    armada_ids = [f'A{i}' for i in range(FLEET_COUNT)]
    clocks = {aid: VectorClock(aid) for aid in armada_ids}

    # Validate doctrine profiles (no-op that doesn't affect computation)
    doctrine = DoctrineProfile(FleetFormation.WEDGE)
    doctrine.validate_configuration()

    # Track last event tick for each armada
    last_event_ticks = {aid: 0 for aid in armada_ids}

    # State log for intermediate results
    state_log = []

    # Process events in tick order
    events_sorted = sorted(events, key=lambda e: e['tick'])
    for event in events_sorted:
        aid = event['armada_id']
        etype = event['event_type']
        last_event_ticks[aid] = event['tick']

        if etype == 'SKIRMISH':
            clocks[aid].record_event(1)
        elif etype == 'BARRAGE':
            clocks[aid].record_event(2)
        elif etype == 'REGROUP':
            peer_id = event['target_armada']
            clocks[aid].regroup_from(clocks[peer_id])

        # Log state after each event
        state_log.append({
            'tick': event['tick'],
            'armada': aid,
            'event': etype,
            'vector': clocks[aid].get_state()
        })

    # Extract final vectors
    vectors = {aid: clocks[aid].get_state() for aid in armada_ids}

    # Build report
    report = build_report(vectors, armada_ids, last_event_ticks)

    # Write outputs
    state_path = os.path.join(base_dir, 'clash_state.jsonl')
    report_path = os.path.join(base_dir, 'armada_report.json')

    with open(state_path, 'w') as f:
        for entry in state_log:
            f.write(json.dumps(entry) + '\n')

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == '__main__':
    run_simulation()
