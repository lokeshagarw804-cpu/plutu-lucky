"""
Repair script for the Lattice Signal Propagation Simulator.

Patches propagation_core.py and lattice_analysis.py to fix signal
depth tracking and isolation classification, then re-runs the pipeline.
"""
import os
import subprocess
import sys


def find_runtime_dir():
    """Locate the runtime directory in either Docker or local context."""
    candidates = [
        '/app/runtime',
        os.path.join(os.path.dirname(__file__), '..', 'runtime'),
    ]
    for path in candidates:
        if os.path.isdir(path):
            return os.path.abspath(path)
    raise RuntimeError("Cannot locate runtime directory")


def patch_file(filepath, old_text, new_text):
    """Apply a string replacement patch to a file."""
    with open(filepath, 'r') as f:
        content = f.read()
    if old_text not in content:
        raise RuntimeError(f"Patch target not found in {filepath}")
    content = content.replace(old_text, new_text, 1)
    with open(filepath, 'w') as f:
        f.write(content)


def main():
    runtime_dir = find_runtime_dir()

    # Fix 1: propagation_core.py - add own-depth increment after relay merge
    core_path = os.path.join(runtime_dir, 'propagation_core.py')
    patch_file(
        core_path,
        '        self._relay_count += 1\n        self._event_count += 1',
        '        self._depth[self.node_id] += 1\n        self._relay_count += 1\n        self._event_count += 1'
    )

    # Fix 2: lattice_analysis.py - isolation uses incomparability, not equality
    analysis_path = os.path.join(runtime_dir, 'lattice_analysis.py')
    patch_file(
        analysis_path,
        '    return vector_leq(depth_a, depth_b) and vector_leq(depth_b, depth_a)',
        '    return not vector_leq(depth_a, depth_b) and not vector_leq(depth_b, depth_a)'
    )

    # Fix 3: lattice_analysis.py - priority by total depth, not wavefront velocity
    patch_file(
        analysis_path,
        '    wavefront_velocity = {}\n'
        '    for node in nodes:\n'
        '        max_depth = max(depths[node])\n'
        '        node_events = [e for e in trace_events if e[\'node_id\'] == node]\n'
        '        first_seq = min(e[\'seq\'] for e in node_events)\n'
        '        last_seq = max(e[\'seq\'] for e in node_events)\n'
        '        time_span = last_seq - first_seq + 1\n'
        '        wavefront_velocity[node] = max_depth / time_span\n'
        '\n'
        '    return sorted(nodes, key=lambda n: wavefront_velocity[n], reverse=True)',
        '    return sorted(nodes, key=lambda n: sum(depths[n]), reverse=True)'
    )

    # Re-run pipeline to regenerate outputs
    pipeline_path = os.path.join(runtime_dir, 'pipeline.py')
    subprocess.run([sys.executable, pipeline_path], check=True)
    print("Repair complete. Pipeline re-executed successfully.")


if __name__ == '__main__':
    main()
