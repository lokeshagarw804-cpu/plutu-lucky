"""
Repair script for the lattice momentum propagation simulator.
Applies patches to fix identified defects and re-runs the simulation.
"""

import sys
import os
import re

RUNTIME_DIR = "/app/runtime"


def patch_momentum_engine():
    """Fix the collision self-increment in momentum_engine.py."""
    filepath = os.path.join(RUNTIME_DIR, "momentum_engine.py")
    with open(filepath, "r") as f:
        content = f.read()

    old = "        self._event_count += 1\n        self._last_step = seq_id\n        self._collision_count += 1\n        self._record_thermal_snapshot()"
    new = "        self._momentum[self.cell_id] += 1\n        self._event_count += 1\n        self._last_step = seq_id\n        self._collision_count += 1\n        self._record_thermal_snapshot()"

    content = content.replace(old, new, 1)

    with open(filepath, "w") as f:
        f.write(content)


def patch_regime_classifier_metric():
    """Fix the symmetric envelope metric in regime_classifier.py."""
    filepath = os.path.join(RUNTIME_DIR, "regime_classifier.py")
    with open(filepath, "r") as f:
        content = f.read()

    content = content.replace(
        "    return forward and reverse",
        "    return not forward and not reverse",
        1
    )

    with open(filepath, "w") as f:
        f.write(content)


def patch_regime_classifier_priority():
    """Fix the relaxation sweep priority in regime_classifier.py."""
    filepath = os.path.join(RUNTIME_DIR, "regime_classifier.py")
    with open(filepath, "r") as f:
        content = f.read()

    old_sort = """    priority = sorted(
        cells.keys(),
        key=lambda x: activity_scores[x] * len(vectors[x]) / (1 + collision_counts[x]),
        reverse=True,
    )"""

    new_sort = """    priority = sorted(
        cells.keys(),
        key=lambda x: sum(vectors[x].values()),
        reverse=True,
    )"""

    content = content.replace(old_sort, new_sort, 1)

    with open(filepath, "w") as f:
        f.write(content)


def rerun_simulation():
    """Re-run the simulation with patched code."""
    output_dir = os.path.join(RUNTIME_DIR, "output")
    if os.path.exists(output_dir):
        import shutil
        shutil.rmtree(output_dir)

    sys.path.insert(0, RUNTIME_DIR)

    # Clear cached modules
    mods_to_remove = [
        m for m in sys.modules
        if m in ("orchestrator", "parser", "momentum_engine",
                 "regime_classifier", "report_writer", "calibration")
    ]
    for m in mods_to_remove:
        del sys.modules[m]

    from orchestrator import main
    main()


if __name__ == "__main__":
    patch_momentum_engine()
    patch_regime_classifier_metric()
    patch_regime_classifier_priority()
    rerun_simulation()
