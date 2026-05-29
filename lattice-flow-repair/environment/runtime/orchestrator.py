"""Orchestrator for lattice flow pressure simulation.

Coordinates the full simulation pipeline: parse trace log, replay
events through the pressure engine, analyze flow relationships,
and generate the final report.
"""
import json
import os
import sys

from trace_parser import parse_trace, parse_couple_state
from pressure_engine import JunctionPressure
from flow_analyzer import analyze_flow_pairs
from report_writer import generate_report


ALL_JUNCTIONS = [
    'junc_alpha', 'junc_beta', 'junc_gamma', 'junc_delta',
    'junc_epsilon', 'junc_zeta', 'junc_eta'
]


def run_simulation(trace_path):
    """Execute the full lattice flow simulation.
    
    Args:
        trace_path: Path to the flow trace log file.
        
    Returns:
        Tuple of (state_records, report) where state_records is a list
        of per-junction state dicts and report is the full analysis report.
    """
    # Parse trace
    events = parse_trace(trace_path)
    
    # Initialize pressure engines for all junctions
    engines = {}
    for jid in ALL_JUNCTIONS:
        engines[jid] = JunctionPressure(jid, ALL_JUNCTIONS)
    
    # Replay events
    for event in events:
        jid = event['junction_id']
        etype = event['event_type']
        
        if etype == 'PUMP':
            engines[jid].apply_pump()
        elif etype == 'SURGE':
            engines[jid].apply_surge()
        elif etype == 'COUPLE':
            neighbor_state = parse_couple_state(event['detail'])
            engines[jid].apply_couple(neighbor_state)
    
    # Collect final vectors
    nodes = sorted(ALL_JUNCTIONS)
    vectors = {}
    for jid in nodes:
        vectors[jid] = engines[jid].get_vector()
    
    # Analyze flow relationships
    analysis = analyze_flow_pairs(nodes, vectors, events)
    
    # Generate report
    report = generate_report(nodes, vectors, analysis, events)
    
    # Build state records
    state_records = []
    for jid in nodes:
        record = {
            'junction_id': jid,
            'pressure_vector': vectors[jid],
            'pressure_map': engines[jid].get_pressure_map(),
            'event_count': sum(1 for e in events if e['junction_id'] == jid)
        }
        state_records.append(record)
    
    return state_records, report


def main():
    """Main entry point for the simulation."""
    trace_path = os.path.join(os.path.dirname(__file__), 'flow_trace.log')
    
    state_records, report = run_simulation(trace_path)
    
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
