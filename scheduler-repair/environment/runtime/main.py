"""
Main entry point for the job scheduler.
Orchestrates dispatch, execution, and reporting stages.
"""

import json
import os

from runtime.dispatcher import dispatch
from runtime.executor import simulate_execution
from runtime.reporter import generate_report


def main():
    assignments = dispatch()
    schedule = simulate_execution(assignments)
    report = generate_report(schedule)

    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    schedule_path = os.path.join(output_dir, "schedule.json")
    with open(schedule_path, "w") as f:
        json.dump(schedule, f, indent=2)

    report_path = os.path.join(output_dir, "report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Schedule written to {schedule_path}")
    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
