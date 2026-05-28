"""
Pipeline Orchestrator
======================
Drives the lattice signal propagation simulation end-to-end:
reads trace events, processes them through the propagation core,
writes intermediate state, and generates the synthesis report.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from trace_reader import read_trace, get_node_ids, parse_payload
from propagation_core import SignalDepthTracker
from synthesis_output import generate_report


def run_pipeline(runtime_dir=None):
    """Execute the full simulation pipeline.

    Args:
        runtime_dir: Directory containing trace log and where outputs
                     will be written. Defaults to the script's directory.
    """
    if runtime_dir is None:
        runtime_dir = os.path.dirname(os.path.abspath(__file__))

    trace_path = os.path.join(runtime_dir, 'signal_trace.log')
    state_path = os.path.join(runtime_dir, 'propagation_state.jsonl')
    report_path = os.path.join(runtime_dir, 'synthesis_report.json')

    # Read trace events
    events = read_trace(trace_path)
    node_ids = get_node_ids(events)

    # Initialize trackers
    trackers = {nid: SignalDepthTracker(nid, node_ids) for nid in node_ids}

    # Process events in sequence order
    sorted_events = sorted(events, key=lambda e: e['seq'])
    for event in sorted_events:
        node = event['node_id']
        etype = event['event_type']
        payload = parse_payload(event['payload'])

        if etype == 'PULSE':
            trackers[node].apply_pulse()
        elif etype == 'BURST':
            trackers[node].apply_burst()
        elif etype == 'RELAY':
            trackers[node].apply_relay(payload['depths'])

    # Finalize all trackers (batch-apply deferred computations)
    for nid in node_ids:
        trackers[nid].finalize_propagation()

    # Write propagation state (JSONL format)
    with open(state_path, 'w') as f:
        for nid in node_ids:
            record = {
                'node_id': nid,
                'depth_vector': trackers[nid].depth_vector,
                'total_depth': trackers[nid].total_depth,
                'event_count': trackers[nid].event_count
            }
            f.write(json.dumps(record) + '\n')

    # Generate synthesis report
    depths = {nid: trackers[nid].vector_as_list for nid in node_ids}
    generate_report(node_ids, depths, events, report_path)

    return state_path, report_path


if __name__ == '__main__':
    state_path, report_path = run_pipeline()
    print(f"Propagation state written to: {state_path}")
    print(f"Synthesis report written to: {report_path}")
