#!/usr/bin/env python3
"""Repair script for particle collision detection system.

Patches defects in runtime source files and re-runs the simulation.
"""
import sys


def patch_hasher():
    """Fix spatial hash grid issues.

    Bug 1: The hash function uses int(x / cell_size) which truncates
    toward zero. For negative coordinates this produces wrong cell
    assignments. Fix: use floor division operator //.

    Bug 4: Neighbor search uses range(-1, 2) giving a 3x3 window.
    With collision_radius=15 and cell_size=10, particles can be up
    to 2 cells apart and still collide. Fix: use range(-2, 3) for 5x5.
    """
    path = "/app/runtime/hasher.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug 1: floor division for correct negative coordinate hashing
    content = content.replace(
        "cell_x = int(x / self._cell_size)",
        "cell_x = int(x // self._cell_size)"
    )
    content = content.replace(
        "cell_y = int(y / self._cell_size)",
        "cell_y = int(y // self._cell_size)"
    )

    # Fix Bug 4: expand neighbor search from 3x3 to 5x5
    content = content.replace(
        "for dx in range(-1, 2):",
        "for dx in range(-2, 3):"
    )
    content = content.replace(
        "for dy in range(-1, 2):",
        "for dy in range(-2, 3):"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_resolver():
    """Fix collision resolver issues.

    Bug 2: History stores single response (overwrite) instead of
    appending to a list. This loses multi-frame collision data.
    Fix: use setdefault with list append.

    Bug 3: Reads restitution from [physics] section (0.8) instead
    of [physics.elastic] section (0.6). Fix: read correct section.
    """
    path = "/app/runtime/resolver.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug 3: correct config section for restitution
    content = content.replace(
        'self._restitution = config.getfloat("physics", "restitution")',
        'self._restitution = config.getfloat("physics.elastic", "restitution")'
    )

    # Fix Bug 2: append to history list instead of overwriting
    content = content.replace(
        "self._history[pair_key] = response",
        "self._history.setdefault(pair_key, []).append(response)"
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_hasher()
    patch_resolver()

    import subprocess
    result = subprocess.run(
        ["python3", "-m", "runtime.main"],
        cwd="/app",
        capture_output=True
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
