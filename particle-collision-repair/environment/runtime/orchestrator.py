"""
Orchestrator
=============
Drives the type inference constraint solver end-to-end:
reads constraint events, processes them through the type engine,
writes intermediate state, and generates the inference report.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from log_reader import read_constraint_log, get_type_ids, parse_payload
from type_engine import ConstraintTracker
from report_writer import generate_report


def run_inference(runtime_dir=None):
    """Execute the full inference pipeline."""
    if runtime_dir is None:
        runtime_dir = os.path.dirname(os.path.abspath(__file__))

    log_path = os.path.join(runtime_dir, 'constraint_log.dat')
    state_path = os.path.join(runtime_dir, 'type_state.jsonl')
    report_path = os.path.join(runtime_dir, 'inference_report.json')

    events = read_constraint_log(log_path)
    type_ids = get_type_ids(events)

    trackers = {tid: ConstraintTracker(tid, type_ids) for tid in type_ids}

    sorted_events = sorted(events, key=lambda e: e['seq'])
    for event in sorted_events:
        tid = event['type_id']
        etype = event['event_type']
        payload = parse_payload(event['payload'])

        if etype == 'BIND':
            trackers[tid].apply_bind()
        elif etype == 'PROPAGATE':
            trackers[tid].apply_propagate()
        elif etype == 'UNIFY':
            trackers[tid].apply_unify(payload['constraints'])

    with open(state_path, 'w') as f:
        for tid in type_ids:
            record = {
                'type_id': tid,
                'constraint_vector': trackers[tid].constraint_vector,
                'total_constraints': trackers[tid].total_constraints,
                'event_count': trackers[tid].event_count
            }
            f.write(json.dumps(record) + '\n')

    constraints = {tid: trackers[tid].vector_as_list for tid in type_ids}
    generate_report(type_ids, constraints, events, report_path)

    return state_path, report_path


if __name__ == '__main__':
    state_path, report_path = run_inference()
    print(f"Type state written to: {state_path}")
    print(f"Inference report written to: {report_path}")
