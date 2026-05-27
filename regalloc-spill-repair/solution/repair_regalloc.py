"""Repair script for the register allocation system.

Fixes four semantic defects across the liveness, simplifier, spill cost,
and coloring modules.
"""

import os


def read_file(path):
    with open(path, "r") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)


def fix_liveness():
    """Fix Bug A: liveness interval endpoints must be exclusive.
    
    The interference module checks overlap with start_a < end_b and start_b < end_a,
    which requires intervals to use exclusive end points (end = last_use + 1).
    """
    path = "/app/runtime/liveness.py"
    content = read_file(path)
    
    # Fix: definitions should set end to global_index + 1
    content = content.replace(
        '                if dest not in intervals:\n'
        '                    intervals[dest] = [global_index, global_index]\n'
        '                else:\n'
        '                    intervals[dest][1] = global_index',
        '                if dest not in intervals:\n'
        '                    intervals[dest] = [global_index, global_index + 1]\n'
        '                else:\n'
        '                    intervals[dest][1] = global_index + 1'
    )
    
    # Fix: uses should also set end to global_index + 1
    content = content.replace(
        '                if src not in intervals:\n'
        '                    intervals[src] = [global_index, global_index]\n'
        '                else:\n'
        '                    intervals[src][1] = global_index',
        '                if src not in intervals:\n'
        '                    intervals[src] = [global_index, global_index + 1]\n'
        '                else:\n'
        '                    intervals[src][1] = global_index + 1'
    )
    
    write_file(path, content)
    print("Fixed liveness.py: intervals now use exclusive end points")


def fix_simplifier():
    """Fix Bug B: simplification threshold must be strict less-than.
    
    A node with degree < K can always be colored. Degree == K is not guaranteed.
    """
    path = "/app/runtime/simplifier.py"
    content = read_file(path)
    
    content = content.replace(
        '            if len(working[var]) <= num_registers:',
        '            if len(working[var]) < num_registers:'
    )
    
    write_file(path, content)
    print("Fixed simplifier.py: degree threshold corrected")


def fix_spill_cost():
    """Fix Bug C: loop depth factor must use exponentiation.
    
    The cost formula should be: (uses + defs) * base_weight^loop_depth / degree
    """
    path = "/app/runtime/spill_cost.py"
    content = read_file(path)
    
    content = content.replace(
        '        # Apply loop depth scaling factor\n'
        '        loop_factor = base_weight * loop_depth if loop_depth > 0 else 1',
        '        # Apply loop depth scaling factor\n'
        '        loop_factor = base_weight ** loop_depth'
    )
    
    write_file(path, content)
    print("Fixed spill_cost.py: loop factor now uses exponentiation")


def fix_coloring():
    """Fix Bug D: uncolored neighbors must not contribute color constraints.
    
    When a neighbor hasn't been colored yet, it should not block any register.
    """
    path = "/app/runtime/coloring.py"
    content = read_file(path)
    
    content = content.replace(
        '        # Collect colors used by all neighbors in the interference graph\n'
        '        used_colors = set()\n'
        '        for neighbor in adjacency.get(var, set()):\n'
        '            color = coloring.get(neighbor)\n'
        '            if color is not None:\n'
        '                used_colors.add(color)\n'
        '            else:\n'
        '                # Conservative constraint for unassigned neighbors\n'
        '                if neighbor in coloring:\n'
        '                    used_colors.add(coloring[neighbor])\n'
        '                else:\n'
        '                    used_colors.add(0)',
        '        # Collect colors used by all neighbors in the interference graph\n'
        '        used_colors = set()\n'
        '        for neighbor in adjacency.get(var, set()):\n'
        '            color = coloring.get(neighbor)\n'
        '            if color is not None:\n'
        '                used_colors.add(color)'
    )
    
    write_file(path, content)
    print("Fixed coloring.py: uncolored neighbors no longer add constraints")


if __name__ == "__main__":
    fix_liveness()
    fix_simplifier()
    fix_spill_cost()
    fix_coloring()
    print("\nAll fixes applied. Re-running allocation...")
    
    # Re-run the allocation to produce correct output
    import sys
    sys.path.insert(0, "/app")
    from runtime.run_regalloc import run
    run()
