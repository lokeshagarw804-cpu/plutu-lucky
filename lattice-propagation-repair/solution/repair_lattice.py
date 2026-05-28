# PLUTU-LUCKY-CANARY
"""Repair script for lattice propagation simulator.

Patches all identified issues in the signal processing pipeline
and re-runs to produce corrected synthesis report.
"""

import os
import subprocess


def patch_file(filepath, replacements):
    """Apply string replacements to a file.

    Args:
        filepath: Path to the file to patch.
        replacements: List of (old_string, new_string) tuples.
    """
    with open(filepath, 'r') as f:
        content = f.read()

    for old, new in replacements:
        if old not in content:
            print(f"WARNING: Could not find pattern in {filepath}:")
            print(f"  {repr(old[:80])}")
            continue
        content = content.replace(old, new)

    with open(filepath, 'w') as f:
        f.write(content)


def main():
    base_dir = '/app/runtime'

    # Patch 1: Fix log base mismatch in attenuation computation
    patch_file(os.path.join(base_dir, 'propagation_core.py'), [
        (
            '    total_log = sum(math.log(a) for a in attenuations)\n'
            '    return 10 ** total_log',
            '    total_log = sum(math.log(a) for a in attenuations)\n'
            '    return math.exp(total_log)'
        ),
    ])

    # Patch 2: Fix phase wraparound ordering
    patch_file(os.path.join(base_dir, 'propagation_core.py'), [
        (
            '        accumulated_phase = accumulated_phase % (2 * math.pi)\n'
            '        hop_phase = phase_shifts[i] + 2 * math.pi * frequency * delays[i]\n'
            '        accumulated_phase += hop_phase',
            '        hop_phase = phase_shifts[i] + 2 * math.pi * frequency * delays[i]\n'
            '        accumulated_phase += hop_phase\n'
            '        accumulated_phase = accumulated_phase % (2 * math.pi)'
        ),
    ])

    # Patch 3: Fix swapped sin/cos in phasor addition
    patch_file(os.path.join(base_dir, 'lattice_analysis.py'), [
        (
            '        real_sum += amp * math.sin(phase)\n'
            '        imag_sum += amp * math.cos(phase)',
            '        real_sum += amp * math.cos(phase)\n'
            '        imag_sum += amp * math.sin(phase)'
        ),
    ])

    # Patch 4: Fix energy normalization at boundaries
    patch_file(os.path.join(base_dir, 'lattice_analysis.py'), [
        (
            '        energy = math.sqrt(sum(s ** 2 for s in window) / window_size)',
            '        energy = math.sqrt(sum(s ** 2 for s in window) / len(window))'
        ),
    ])

    # Patch 5: Fix visited set not restored on early return
    patch_file(os.path.join(base_dir, 'topology_resolver.py'), [
        (
            '        if len(neighbors) == 1 and neighbors[0] == target:\n'
            '            paths.append(current_path + [target])\n'
            '            return',
            '        if len(neighbors) == 1 and neighbors[0] == target:\n'
            '            paths.append(current_path + [target])\n'
            '            visited.discard(node)\n'
            '            return'
        ),
    ])

    # Patch 6: Fix missing Nyquist in pre-warping
    patch_file(os.path.join(base_dir, 'signal_filter.py'), [
        (
            '    omega_low = 2.0 * math.pi * freq_low / sampling_rate\n'
            '    omega_high = 2.0 * math.pi * freq_high / sampling_rate',
            '    omega_low = 2.0 * math.pi * freq_low / (sampling_rate / 2)\n'
            '    omega_high = 2.0 * math.pi * freq_high / (sampling_rate / 2)'
        ),
    ])

    # Patch 7: Fix floor vs round in time quantization
    patch_file(os.path.join(base_dir, 'calibration.py'), [
        (
            '    bin_index = int(arrival_time / time_step)\n'
            '    return bin_index',
            '    bin_index = round(arrival_time / time_step)\n'
            '    return bin_index'
        ),
    ])

    # Re-run the pipeline with fixes applied
    subprocess.run(
        ['python3', '-m', 'runtime.pipeline'],
        cwd='/app',
        check=True
    )
    print("Pipeline executed successfully with all patches applied.")


if __name__ == '__main__':
    main()
