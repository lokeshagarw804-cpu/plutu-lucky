"""
Main entry point for the three-way merge engine.

Orchestrates the merge process:
1. Load base, branch_a, and branch_b document versions
2. Compute diffs between base and each branch
3. Detect conflicts between branch changes
4. Resolve conflicts using configured strategy
5. Assemble final merged document
6. Write output files
"""

import json
import os
import configparser

from runtime.diff_engine import compute_section_diff
from runtime.conflict_detector import detect_conflicts
from runtime.resolver import ConflictResolver
from runtime.assembler import assemble_section


def load_document(filepath):
    """Load a document version from JSON."""
    with open(filepath, "r") as f:
        return json.load(f)


def main():
    """Run the three-way merge process."""
    config = configparser.ConfigParser()
    config.read("/app/runtime/config.ini")

    data_dir = "/app/runtime/data"
    base = load_document(os.path.join(data_dir, "document_base.json"))
    branch_a = load_document(os.path.join(data_dir, "document_branch_a.json"))
    branch_b = load_document(os.path.join(data_dir, "document_branch_b.json"))

    resolver = ConflictResolver()

    merged_sections = []
    all_conflicts = []
    total_auto_resolved = 0
    total_conflicts = 0

    for i, base_section in enumerate(base["sections"]):
        section_id = base_section["id"]
        base_lines = base_section["lines"]

        # Find matching sections in branches
        a_section = next(
            (s for s in branch_a["sections"] if s["id"] == section_id),
            base_section
        )
        b_section = next(
            (s for s in branch_b["sections"] if s["id"] == section_id),
            base_section
        )

        # Compute diffs
        regions_a = compute_section_diff(base_lines, a_section["lines"])
        regions_b = compute_section_diff(base_lines, b_section["lines"])

        # Detect conflicts
        conflicts, auto_a, auto_b = detect_conflicts(regions_a, regions_b)

        # Resolve conflicts
        resolutions = resolver.resolve_conflicts(conflicts, base_lines)

        # Assemble merged section
        merged_lines = assemble_section(
            base_lines, resolutions, auto_a, auto_b
        )

        merged_sections.append({
            "id": section_id,
            "title": base_section["title"],
            "lines": merged_lines,
        })

        total_conflicts += len(conflicts)
        total_auto_resolved += len(auto_a) + len(auto_b)

        for conf in conflicts:
            all_conflicts.append({
                "section_id": section_id,
                "region_a": conf[0].to_dict(),
                "region_b": conf[1].to_dict(),
            })

    # Write outputs
    output_dir = os.path.dirname(config.get("output", "merged_path"))
    os.makedirs(output_dir, exist_ok=True)

    merged_doc = {
        "doc_id": base["doc_id"],
        "version": "merged",
        "sections": merged_sections,
    }

    conflict_report = {
        "total_conflicts": total_conflicts,
        "total_auto_resolved": total_auto_resolved,
        "conflict_details": all_conflicts,
    }

    summary = {
        "sections_processed": len(base["sections"]),
        "total_conflicts": total_conflicts,
        "total_auto_resolved": total_auto_resolved,
        "merged_section_line_counts": {
            s["id"]: len(s["lines"]) for s in merged_sections
        },
    }

    with open(config.get("output", "merged_path"), "w") as f:
        json.dump(merged_doc, f, indent=2)
    with open(config.get("output", "conflicts_path"), "w") as f:
        json.dump(conflict_report, f, indent=2)
    with open(config.get("output", "summary_path"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Merged {summary['sections_processed']} sections")
    print(f"Conflicts: {total_conflicts}")
    print(f"Auto-resolved: {total_auto_resolved}")


if __name__ == "__main__":
    main()
