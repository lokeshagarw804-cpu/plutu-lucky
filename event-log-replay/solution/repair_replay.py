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

    # Fix 1: causality.py — remove skip_node check in clock comparison
    patch_file(
        os.path.join(runtime_dir, "causality.py"),
        [
            (
                "        for node in all_nodes:\n"
                "            # BUG: skip_node causes incomplete comparison\n"
                "            if node == self._skip_node:\n"
                "                continue\n"
                "            val_a = clock_a.get(node, 0)",
                "        for node in all_nodes:\n"
                "            val_a = clock_a.get(node, 0)"
            ),
        ]
    )

    # Fix 2: causality.py — drift check should be inclusive (< to <=)
    patch_file(
        os.path.join(runtime_dir, "causality.py"),
        [
            (
                "                        # BUG: should be <= (inclusive of boundary)\n"
                "                        if time_diff < self._max_drift:",
                "                        if time_diff <= self._max_drift:"
            ),
        ]
    )

    # Fix 3: loader.py — window boundary inclusive (<= instead of <) and remove dead elif
    patch_file(
        os.path.join(runtime_dir, "loader.py"),
        [
            (
                "            # BUG: should be <= for inclusive boundary\n"
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

    # Fix 4: reporter.py — accumulate weight instead of overwriting
    patch_file(
        os.path.join(runtime_dir, "reporter.py"),
        [
            (
                "                # BUG: should be total_weight += weight\n"
                "                total_weight = weight",
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
