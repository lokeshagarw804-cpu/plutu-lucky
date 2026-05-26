"""
Repair script for the job scheduler.
Fixes three bugs in the scheduling system and re-runs to produce correct output.
"""

import subprocess
import os


def fix_dispatcher():
    """Fix priority sort order in dispatcher.py."""
    path = "/app/runtime/dispatcher.py"
    with open(path, "r") as f:
        source = f.read()

    old = 'sorted_jobs = sorted(jobs, key=lambda j: (-j["priority"], j["deadline_ms"]))'
    new = 'sorted_jobs = sorted(jobs, key=lambda j: (j["priority"], j["deadline_ms"]))'

    assert old in source, "Could not find dispatcher sort line to fix"
    source = source.replace(old, new)

    with open(path, "w") as f:
        f.write(source)
    print("[fix] dispatcher.py: corrected priority sort order")


def fix_executor():
    """Fix deadline comparison in executor.py."""
    path = "/app/runtime/executor.py"
    with open(path, "r") as f:
        source = f.read()

    old = "on_time = finish_ms < deadline"
    new = "on_time = finish_ms <= deadline"

    assert old in source, "Could not find executor deadline check to fix"
    source = source.replace(old, new)

    with open(path, "w") as f:
        f.write(source)
    print("[fix] executor.py: corrected deadline comparison to inclusive")


def fix_reporter():
    """Fix worker utilization accumulation in reporter.py."""
    path = "/app/runtime/reporter.py"
    with open(path, "r") as f:
        source = f.read()

    old = "        total_time = job_time\n        worker_times[worker] = total_time"
    new = "        worker_times[worker] += job_time"

    assert old in source, "Could not find reporter accumulation bug to fix"
    source = source.replace(old, new)

    with open(path, "w") as f:
        f.write(source)
    print("[fix] reporter.py: corrected worker time accumulation")


def main():
    fix_dispatcher()
    fix_executor()
    fix_reporter()

    # Remove stale output
    output_dir = "/app/runtime/output"
    if os.path.isdir(output_dir):
        for fname in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, fname))

    # Re-run the scheduler
    result = subprocess.run(
        ["python3", "-m", "runtime.main"],
        cwd="/app",
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError(f"Scheduler failed with code {result.returncode}")

    print("[done] Scheduler re-run complete, output written.")


if __name__ == "__main__":
    main()
