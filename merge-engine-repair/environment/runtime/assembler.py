"""
Document assembler.

Reconstructs the merged document by applying resolved changes and
auto-resolved regions to the base document. Processes sections in
order, applying non-overlapping changes directly and using
resolution decisions for conflicting regions.
"""


def assemble_section(base_lines, resolutions, auto_a, auto_b):
    """Assemble a merged section from base lines and changes.

    Applies auto-resolved changes and conflict resolutions to
    produce the final merged line list for a section.
    """
    # Collect all changes with their positions
    changes = []

    for resolution in resolutions:
        changes.append({
            "start": resolution["start"],
            "end": resolution["end"],
            "lines": resolution["resolved_lines"],
            "type": "resolution",
        })

    for region in auto_a + auto_b:
        changes.append({
            "start": region.start,
            "end": region.end,
            "lines": region.replacement_lines,
            "type": region.change_type,
        })

    # Sort changes by start position (process from end to avoid index shift)
    changes.sort(key=lambda c: c["start"], reverse=True)

    merged = list(base_lines)

    for change in changes:
        start = change["start"]
        end = change["end"]

        if change["type"] == "add":
            # Insert additions after the start position
            for idx, line in enumerate(change["lines"]):
                merged.insert(start + idx, line)
        elif change["type"] == "delete":
            del merged[start:end]
        else:
            # Replace the region with resolved lines
            merged[start:end] = change["lines"]

    return merged
