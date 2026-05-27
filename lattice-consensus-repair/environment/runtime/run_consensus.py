"""Lattice consensus analyzer — main entry point.

Orchestrates the full consensus analysis: load validator logs, build the
transaction DAG lattice, compute confirmation weights, check finality
status, and generate the consensus report.
"""
import json
import os

from runtime.loader import ValidatorLoader
from runtime.dag_builder import DagBuilder
from runtime.weight_calculator import WeightCalculator
from runtime.finality_checker import FinalityChecker
from runtime.consensus_reporter import ConsensusReporter


def main():
    config_path = "/app/runtime/config.ini"

    # Load validator transaction logs
    loader = ValidatorLoader(config_path)
    validators = loader.load_validators()

    # Build unified DAG
    builder = DagBuilder()
    all_txs, children, tx_lookup = builder.build_lattice(validators)

    # Compute confirmation weights
    calculator = WeightCalculator(config_path)
    tx_weights = calculator.compute_weights(
        all_txs, children, tx_lookup, validators
    )

    # Check finality
    checker = FinalityChecker(config_path)
    finality = checker.check_finality(
        all_txs, tx_weights, children, tx_lookup, validators
    )

    # Prepare transaction list for reporting in canonical order
    report_txs = sorted(all_txs, key=lambda t: t["tx_id"])

    # Generate reports
    reporter = ConsensusReporter()
    finality_map, summary = reporter.generate_report(
        report_txs, finality, validators, tx_weights
    )

    # Write outputs
    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "finality_map.json"), "w") as f:
        json.dump(finality_map, f, indent=2)

    with open(os.path.join(output_dir, "consensus_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Processed {summary['total_transactions']} transactions")
    print(f"Finalized: {summary['total_finalized']}")
    print(f"Validators: {summary['total_validators']}")
    print(f"Rounds: {summary['rounds_processed']}")


if __name__ == "__main__":
    main()
