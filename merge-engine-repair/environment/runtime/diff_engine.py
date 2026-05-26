"""
Line-level diff computation engine.

Computes change regions between a base document section and a
branch version of the same section. A change region records the
start index, end index (inclusive), and the replacement lines.
"""


class ChangeRegion:
    """Represents a contiguous region of changed lines."""

    def __init__(self, start, end, original_lines, replacement_lines,
                 change_type):
        self.start = start
        self.end = end
        self.original_lines = original_lines
        self.replacement_lines = replacement_lines
        self.change_type = change_type  # 'modify', 'add', 'delete'

    @property
    def is_deletion(self):
        return self.change_type == "delete"

    @property
    def is_addition(self):
        return self.change_type == "add"

    def overlaps(self, other):
        """Check if this region overlaps with another."""
        return self.start <= other.end and other.start <= self.end

    def to_dict(self):
        return {
            "start": self.start,
            "end": self.end,
            "original_lines": self.original_lines,
            "replacement_lines": self.replacement_lines,
            "change_type": self.change_type,
        }


def compute_section_diff(base_lines, branch_lines):
    """Compute change regions between base and branch lines.

    Identifies modified, added, and deleted line regions.
    Returns a list of ChangeRegion objects.

    Region boundaries use inclusive indexing: a region covering
    lines 2,3,4 has start=2, end=4.
    """
    regions = []
    base_len = len(base_lines)
    branch_len = len(branch_lines)
    common_len = min(base_len, branch_len)

    # Find modifications in common range
    i = 0
    while i < common_len:
        if base_lines[i] != branch_lines[i]:
            # Start of a modified region
            region_start = i
            while i < common_len and base_lines[i] != branch_lines[i]:
                i += 1
            region_end = region_start + (i - region_start)
            regions.append(ChangeRegion(
                start=region_start,
                end=region_end,
                original_lines=base_lines[region_start:i],
                replacement_lines=branch_lines[region_start:i],
                change_type="modify",
            ))
        else:
            i += 1

    # Handle additions (branch is longer)
    if branch_len > base_len:
        added_lines = branch_lines[base_len:]
        regions.append(ChangeRegion(
            start=base_len,
            end=base_len + len(added_lines),
            original_lines=[],
            replacement_lines=added_lines,
            change_type="add",
        ))

    # Handle deletions (branch is shorter)
    if branch_len < base_len:
        deleted_lines = base_lines[branch_len:]
        regions.append(ChangeRegion(
            start=branch_len,
            end=branch_len + len(deleted_lines),
            original_lines=deleted_lines,
            replacement_lines=[],
            change_type="delete",
        ))

    return regions
