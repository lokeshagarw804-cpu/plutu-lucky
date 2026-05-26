"""
Conflict detection module.

Identifies cases where both branches modified overlapping regions
of the same section. A conflict occurs when branch A and branch B
have change regions that overlap AND neither is a pure addition
to the end of the section.

Non-overlapping changes and pure additions are considered
auto-resolvable (no human intervention needed).
"""


def detect_conflicts(regions_a, regions_b):
    """Detect conflicts between two sets of change regions.

    A conflict exists when:
    - Two regions overlap in their line ranges, AND
    - Neither region is a pure addition (appended lines)

    Returns a tuple: (conflicts, auto_resolved_a, auto_resolved_b)
    where conflicts is a list of (region_a, region_b) pairs, and
    auto_resolved lists contain non-conflicting changes.
    """
    conflicts = []
    conflicting_a = set()
    conflicting_b = set()

    for i, ra in enumerate(regions_a):
        for j, rb in enumerate(regions_b):
            if _is_conflict(ra, rb):
                conflicts.append((ra, rb))
                conflicting_a.add(i)
                conflicting_b.add(j)

    auto_a = [r for i, r in enumerate(regions_a) if i not in conflicting_a]
    auto_b = [r for i, r in enumerate(regions_b) if i not in conflicting_b]

    return conflicts, auto_a, auto_b


def _is_conflict(region_a, region_b):
    """Determine if two regions constitute a merge conflict.

    Conditions for conflict:
    1. The regions overlap in line range
    2. Neither is a pure addition (appended content)

    Both conditions must be true for a conflict.
    """
    has_overlap = region_a.overlaps(region_b)
    either_is_addition = region_a.is_addition or region_b.is_addition

    return not has_overlap or either_is_addition
