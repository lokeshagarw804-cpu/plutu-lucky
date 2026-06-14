"""Repair script — patches all bugs in the event-log-replay pipeline."""
import os
import subprocess
import sys


def patch_file(filepath, replacements):
    with open(filepath, "r") as f:
        content = f.read()
    for old, new in replacements:
        if old not in content:
            print(f"WARNING: patch target not found in {filepath}")
            print(f"  Looking for: {repr(old[:80])}")
            continue
        content = content.replace(old, new)
    with open(filepath, "w") as f:
        f.write(content)
    print(f"Patched: {filepath}")


def main():
    runtime_dir = "/app/runtime"

    # Fix 1: causality.py — remove skip_node filter from clock comparison
    patch_file(
        os.path.join(runtime_dir, "causality.py"),
        [
            (
                "        for node in all_nodes:\n"
                "            if node == self._skip_node:\n"
                "                continue\n"
                "            val_a = clock_a.get(node, 0)",
                "        for node in all_nodes:\n"
                "            val_a = clock_a.get(node, 0)"
            ),
        ]
    )

    # Fix 2: causality.py — drift threshold must be inclusive
    patch_file(
        os.path.join(runtime_dir, "causality.py"),
        [
            (
                "                        if time_diff < self._max_drift:",
                "                        if time_diff <= self._max_drift:"
            ),
        ]
    )

    # Fix 3: loader.py — window boundary inclusive and remove dead elif
    patch_file(
        os.path.join(runtime_dir, "loader.py"),
        [
            (
                "            if delta < self._window_ms:\n"
                "                current_group.append(event)\n"
                "            elif delta == self._window_ms and event[\"node_id\"] < current_group[0][\"node_id\"]:\n"
                "                # Node-priority tiebreaker for boundary events\n"
                "                current_group.append(event)\n"
                "            else:",
                "            if delta <= self._window_ms:\n"
                "                current_group.append(event)\n"
                "            else:"
            ),
        ]
    )

    # Fix 4: reporter.py — accumulate weight
    patch_file(
        os.path.join(runtime_dir, "reporter.py"),
        [
            (
                "                weighted_sum += weight * combined\n"
                "                total_weight = weight",
                "                weighted_sum += weight * combined\n"
                "                total_weight += weight"
            ),
        ]
    )

    # Re-run the pipeline with fixes applied
    print("\nRunning fixed pipeline...")
    result = subprocess.run(
        [sys.executable, "-m", "runtime.main"],
        cwd="/app",
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"STDERR: {result.stderr}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
