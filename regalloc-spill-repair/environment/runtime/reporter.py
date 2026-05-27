"""Generate allocation reports and summaries."""

import json
import os


def generate_report(allocation, intervals, adjacency, spill_costs, output_dir):
    """Generate the full allocation report.
    
    Writes:
      - allocation_report.json: detailed allocation for each variable
      - summary.txt: human-readable summary
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Build detailed report
    report = {
        "variables": {},
        "statistics": {},
    }
    
    num_allocated = 0
    num_spilled = 0
    registers_used = set()
    
    for var, info in sorted(allocation.items()):
        report["variables"][var] = {
            "register": info["register"],
            "color": info["color"],
            "spilled": info["spilled"],
            "interval": list(intervals.get(var, (0, 0))),
            "degree": len(adjacency.get(var, set())),
            "spill_cost": spill_costs.get(var, 0),
        }
        
        if info["spilled"]:
            num_spilled += 1
        else:
            num_allocated += 1
            registers_used.add(info["color"])
    
    report["statistics"] = {
        "total_variables": len(allocation),
        "allocated": num_allocated,
        "spilled": num_spilled,
        "registers_used": len(registers_used),
        "max_register": max(registers_used) if registers_used else -1,
    }
    
    # Write JSON report
    report_path = os.path.join(output_dir, "allocation_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    # Write summary
    summary_path = os.path.join(output_dir, "summary.txt")
    with open(summary_path, "w") as f:
        f.write("Register Allocation Summary\n")
        f.write("=" * 40 + "\n")
        f.write(f"Total variables: {len(allocation)}\n")
        f.write(f"Allocated to registers: {num_allocated}\n")
        f.write(f"Spilled to memory: {num_spilled}\n")
        f.write(f"Registers used: {len(registers_used)}\n")
        f.write("\nAllocation Details:\n")
        f.write("-" * 40 + "\n")
        
        for var, info in sorted(allocation.items()):
            if info["spilled"]:
                f.write(f"  {var}: SPILLED (cost={spill_costs.get(var, 0)})\n")
            else:
                f.write(f"  {var}: {info['register']}\n")
    
    return report
