# PLUTU-LUCKY-CANARY
"""Main pipeline for lattice signal propagation simulation.

Orchestrates: load topology -> load traces -> resolve paths ->
propagate signals -> filter -> compute interference -> calibrate ->
aggregate -> write synthesis report.
"""

import json
import os
import configparser
import math

from runtime.propagation_core import propagate_signal
from runtime.lattice_analysis import (
    compute_interference, compute_node_energy, detect_resonance
)
from runtime.topology_resolver import build_adjacency, find_all_paths, get_path_edges
from runtime.signal_filter import bandpass_filter
from runtime.calibration import calibrate_arrivals
from runtime.aggregator import (
    aggregate_results, write_report, merge_node_energies, format_delay_key
)


def load_config(config_path):
    """Load simulation configuration from INI file."""
    config = configparser.ConfigParser()
    config.read(config_path)
    return config


def load_topology(data_dir):
    """Load lattice topology from JSON."""
    path = os.path.join(data_dir, 'topology.json')
    with open(path, 'r') as f:
        return json.load(f)


def load_traces(data_dir):
    """Load all signal trace files from data directory."""
    traces = []
    for fname in sorted(os.listdir(data_dir)):
        if fname.startswith('trace_') and fname.endswith('.json'):
            path = os.path.join(data_dir, fname)
            with open(path, 'r') as f:
                traces.append(json.load(f))
    return traces


def generate_node_samples(trace, propagated, sampling_rate, num_samples):
    """Generate time-domain samples at a destination node from a propagated signal."""
    samples = []
    for i in range(num_samples):
        t = i / sampling_rate
        value = propagated['amplitude'] * math.sin(
            2 * math.pi * propagated['frequency'] * t + propagated['phase']
        )
        samples.append(value)
    return samples


def main():
    """Run the full lattice propagation simulation pipeline."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, 'config.ini')
    data_dir = os.path.join(base_dir, 'data')
    output_path = os.path.join(base_dir, 'output', 'synthesis_report.json')

    config = load_config(config_path)

    time_step = config.getfloat('simulation', 'time_step')
    total_time = config.getfloat('simulation', 'total_time')
    sampling_rate = config.getfloat('simulation', 'sampling_rate')
    bandpass_low = config.getfloat('filter', 'bandpass_low')
    bandpass_high = config.getfloat('filter', 'bandpass_high')
    max_hops = config.getint('propagation', 'max_hops')
    window_size = config.getint('analysis', 'window_size')
    energy_threshold = config.getfloat('analysis', 'energy_threshold')

    num_samples = int(total_time * sampling_rate)

    topology = load_topology(data_dir)
    traces = load_traces(data_dir)
    adjacency = build_adjacency(topology)

    target_node = 6

    all_node_signals = {str(i): [] for i in range(topology['num_nodes'])}
    all_propagation_delays = {}
    total_paths_found = 0

    for trace in traces:
        source = trace['source_node']
        paths = find_all_paths(adjacency, source, target_node, max_hops)
        total_paths_found += len(paths)

        for path in paths:
            edges = get_path_edges(adjacency, path)
            if not edges:
                continue

            propagated = propagate_signal(trace, edges)

            arrival_time = trace['injection_time'] + propagated['delay']
            propagated['delay'] = arrival_time

            dest = path[-1]
            for intermediate_idx in range(1, len(path)):
                node = path[intermediate_idx]
                partial_edges = edges[:intermediate_idx]
                partial_prop = propagate_signal(trace, partial_edges)
                partial_delay = trace['injection_time'] + partial_prop['delay']
                partial_prop['delay'] = partial_delay

                node_samples = generate_node_samples(
                    trace, partial_prop, sampling_rate, num_samples
                )
                filtered = bandpass_filter(
                    node_samples, bandpass_low, bandpass_high, sampling_rate
                )
                all_node_signals[str(node)].append({
                    'amplitude': partial_prop['amplitude'],
                    'phase': partial_prop['phase'],
                    'delay': partial_delay,
                    'frequency': partial_prop['frequency'],
                    'filtered_samples': filtered
                })

            delay_key = format_delay_key(source, dest)
            if delay_key not in all_propagation_delays:
                all_propagation_delays[delay_key] = propagated['delay']
            else:
                all_propagation_delays[delay_key] = min(
                    all_propagation_delays[delay_key], propagated['delay']
                )

    source_nodes = set(t['source_node'] for t in traces)
    for trace in traces:
        src = trace['source_node']
        node_samples = []
        for i in range(num_samples):
            t = i / sampling_rate
            value = trace['amplitude'] * math.sin(
                2 * math.pi * trace['frequency'] * t + trace['phase_offset']
            )
            node_samples.append(value)
        filtered_src = bandpass_filter(
            node_samples, bandpass_low, bandpass_high, sampling_rate
        )
        all_node_signals[str(src)].append({
            'amplitude': trace['amplitude'],
            'phase': trace['phase_offset'],
            'delay': trace['injection_time'],
            'frequency': trace['frequency'],
            'filtered_samples': filtered_src
        })

    node_energies = {}
    for node_id, signals in all_node_signals.items():
        if not signals:
            node_energies[node_id] = 0.0
            continue
        combined_samples = [0.0] * num_samples
        for sig in signals:
            for i, s in enumerate(sig['filtered_samples']):
                combined_samples[i] += s
        energy = compute_node_energy(combined_samples, window_size)
        node_energies[node_id] = energy

    interference_results = {}
    for node_id, signals in all_node_signals.items():
        if len(signals) >= 2:
            binned = calibrate_arrivals(signals, time_step)
            node_interference = {'magnitude': 0.0, 'phase': 0.0}
            for bin_idx, bin_signals in binned.items():
                if len(bin_signals) >= 2:
                    result = compute_interference(bin_signals)
                    if result['magnitude'] > node_interference['magnitude']:
                        node_interference = result
            interference_results[node_id] = node_interference

    resonant_nodes = detect_resonance(node_energies, energy_threshold)

    report = aggregate_results(
        node_energies, all_propagation_delays, interference_results,
        total_paths_found, resonant_nodes
    )

    write_report(report, output_path)


if __name__ == '__main__':
    main()
