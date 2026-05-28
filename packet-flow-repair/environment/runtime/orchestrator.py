"""Orchestrator for distributed sensor network observation simulation.

Coordinates the full simulation pipeline: parse capture log, replay
events through the observation engine, analyze flow relationships,
and generate the final report.
"""
import json
import os
import sys

from log_parser import parse_log, parse_sync_state
from observation_engine import SensorObservation
from flow_classifier import analyze_flow_pairs
from report_generator import generate_report


ALL_SENSORS = [
    'sensor_core', 'sensor_east', 'sensor_edge', 'sensor_gate',
    'sensor_north', 'sensor_south', 'sensor_west'
]


def run_simulation(log_path):
    """Execute the full sensor network observation simulation.
    
    Args:
        log_path: Path to the capture log file.
        
    Returns:
        Tuple of (state_records, report) where state_records is a list
        of per-sensor state dicts and report is the full analysis report.
    """
    # Parse capture log
    events = parse_log(log_path)
    
    # Initialize observation engines for all sensors
    engines = {}
    for sid in ALL_SENSORS:
        engines[sid] = SensorObservation(sid, ALL_SENSORS)
    
    # Replay events
    for event in events:
        sid = event['sensor_id']
        etype = event['event_type']
        
        if etype == 'SCAN':
            engines[sid].apply_scan()
        elif etype == 'PROBE':
            engines[sid].apply_probe()
        elif etype == 'SYNC':
            neighbor_state = parse_sync_state(event['detail'])
            engines[sid].apply_sync(neighbor_state)
    
    # Collect final vectors
    nodes = sorted(ALL_SENSORS)
    vectors = {}
    for sid in nodes:
        vectors[sid] = engines[sid].get_vector()
    
    # Analyze flow relationships
    analysis = analyze_flow_pairs(nodes, vectors, events)
    
    # Generate report
    report = generate_report(nodes, vectors, analysis, events)
    
    # Build state records
    state_records = []
    for sid in nodes:
        record = {
            'sensor_id': sid,
            'observation_vector': vectors[sid],
            'observation_map': engines[sid].get_observation_map(),
            'event_count': sum(1 for e in events if e['sensor_id'] == sid)
        }
        state_records.append(record)
    
    return state_records, report


def main():
    """Main entry point for the simulation."""
    log_path = os.path.join(os.path.dirname(__file__), 'capture_log.dat')
    
    state_records, report = run_simulation(log_path)
    
    # Write state file (JSONL format)
    output_dir = os.path.dirname(__file__)
    state_path = os.path.join(output_dir, 'flow_state.jsonl')
    with open(state_path, 'w') as f:
        for record in state_records:
            f.write(json.dumps(record) + '\n')
    
    # Write report
    report_path = os.path.join(output_dir, 'flow_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Simulation complete. State: {state_path}, Report: {report_path}")


if __name__ == '__main__':
    main()
