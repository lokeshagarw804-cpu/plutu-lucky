"""Repair script for armada clash simulation.

Analyzes the engagement processing pipeline and applies corrections
to restore correct operational semantics.
"""
import os
import subprocess


def repair_vector_engine():
    """Fix the regroup synchronization in vector_engine.py.

    Analysis: The regroup_from method merges peer state but fails to
    record the regroup as a local event. Each synchronization is itself
    an engagement that should advance the local component.
    """
    filepath = '/app/runtime/vector_engine.py'
    with open(filepath, 'r') as f:
        content = f.read()

    old = '''        for i in range(self.fleet_count):
            self._state[i] = max(self._state[i], peer_clock._state[i])
        # NOTE: own component increment is intentionally omitted here.'''

    new = '''        for i in range(self.fleet_count):
            self._state[i] = max(self._state[i], peer_clock._state[i])
        self._state[int(self.entity_id[1:])] += 1
        # NOTE: own component increment is intentionally omitted here.'''

    content = content.replace(old, new)
    with open(filepath, 'w') as f:
        f.write(content)


def repair_clash_analyzer():
    """Fix autonomy predicate and deployment priority in clash_analyzer.py.

    Analysis: The autonomy check uses bidirectional containment (equality)
    rather than incomparability. Deployment uses temporal recency instead
    of engagement weight.
    """
    filepath = '/app/runtime/clash_analyzer.py'
    with open(filepath, 'r') as f:
        content = f.read()

    # Fix autonomy predicate: replace equality check with incomparability
    old_autonomy = '''    # Bidirectional containment check - standard autonomy criterion
    forward = all(a <= b for a, b in zip(vec_a, vec_b))
    backward = all(b <= a for a, b in zip(vec_a, vec_b))
    return forward and backward'''

    new_autonomy = '''    # Incomparability check - neither fleet dominates the other
    return not dominates(vec_a, vec_b) and not dominates(vec_b, vec_a)'''

    content = content.replace(old_autonomy, new_autonomy)

    # Fix deployment priority: replace timestamp sort with vector weight
    old_priority = '''    # Sort by last engagement timestamp - most recently active first
    return sorted(armada_ids, key=lambda x: last_event_ticks[x], reverse=True)'''

    new_priority = '''    # Sort by total engagement weight - highest logical weight first
    return sorted(armada_ids, key=lambda x: sum(vectors[x]), reverse=True)'''

    content = content.replace(old_priority, new_priority)

    with open(filepath, 'w') as f:
        f.write(content)


def main():
    """Apply all repairs and regenerate outputs."""
    # Remove stale outputs
    for fname in ['clash_state.jsonl', 'armada_report.json']:
        path = os.path.join('/app/runtime', fname)
        if os.path.exists(path):
            os.remove(path)

    # Apply repairs
    repair_vector_engine()
    repair_clash_analyzer()

    # Regenerate outputs with fixed code
    subprocess.run(
        ['python3', '/app/runtime/orchestrator.py'],
        check=True
    )
    print("Repairs applied and simulation re-executed successfully.")


if __name__ == '__main__':
    main()
