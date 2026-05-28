# PLUTU-LUCKY-CANARY
"""
Consensus Ledger Verification Pipeline - Orchestrates the full verification
flow including Merkle computation, quorum verification, Byzantine detection,
state machine processing, and balance reconciliation.
"""

import json
import os
import configparser
from typing import Dict, Any

from runtime.crypto_utils import compute_state_hash, batch_hash
from runtime.validator_registry import ValidatorRegistry
from runtime.audit_trail import AuditLogger
from runtime.merkle_engine import compute_batch_roots
from runtime.quorum_verifier import verify_all_rounds, compute_quorum_summary
from runtime.byzantine_detector import detect_byzantine_validators
from runtime.state_machine import process_transactions
from runtime.balance_reconciler import reconcile_balances


def load_config() -> configparser.ConfigParser:
    """Load pipeline configuration from config.ini."""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), "config.ini")
    config.read(config_path)
    return config


def load_data(data_dir: str) -> Dict[str, Any]:
    """Load all data files from the data directory."""
    with open(os.path.join(data_dir, "transactions.json")) as f:
        tx_data = json.load(f)
    with open(os.path.join(data_dir, "validators.json")) as f:
        val_data = json.load(f)
    with open(os.path.join(data_dir, "voting_records.json")) as f:
        vote_data = json.load(f)
    return {
        "transactions": tx_data["transactions"],
        "validators": val_data["validators"],
        "voting_records": vote_data["voting_records"],
        "round_proposals": vote_data["round_proposals"],
    }


def run_pipeline() -> dict:
    """Execute the full consensus verification pipeline."""
    config = load_config()
    batch_size = config.getint("merkle", "batch_size", fallback=10)
    fee_rate = config.getfloat("state_machine", "fee_rate", fallback=0.001)
    initial_balance = config.getint("state_machine", "initial_balance", fallback=1000000)

    data_dir = os.path.join(os.path.dirname(__file__), "data")
    data = load_data(data_dir)

    registry = ValidatorRegistry(data["validators"])
    logger = AuditLogger("consensus_pipeline")

    logger.log_operation("pipeline_start", {
        "transactions": len(data["transactions"]),
        "validators": registry.validator_count,
        "rounds": len(data["round_proposals"]),
    })

    # Step 1: Merkle batch roots
    logger.log_state_transition("init", "merkle_computation", "pipeline_start")
    merkle_roots = compute_batch_roots(data["transactions"], batch_size)
    logger.log_verification("merkle_roots", len(merkle_roots) > 0, {
        "batch_count": len(merkle_roots)
    })

    # Step 2: Quorum verification
    logger.log_state_transition("merkle_computation", "quorum_verification", "merkle_complete")
    round_proposals = data["round_proposals"]
    rounds_data = [
        {"round_id": int(rid), "proposal_hash": phash}
        for rid, phash in sorted(round_proposals.items(), key=lambda x: int(x[0]))
    ]
    quorum_results = verify_all_rounds(registry, rounds_data, data["voting_records"])
    quorum_summary = compute_quorum_summary(quorum_results)
    logger.log_verification("quorum", quorum_summary["all_quorums_met"], {
        "met": quorum_summary["quorum_met_count"],
        "total": quorum_summary["total_rounds"],
    })

    # Step 3: Byzantine detection
    logger.log_state_transition("quorum_verification", "byzantine_detection", "quorum_complete")
    int_round_proposals = {int(k): v for k, v in round_proposals.items()}
    byzantine_result = detect_byzantine_validators(
        registry, data["voting_records"], int_round_proposals
    )
    logger.log_verification("byzantine_detection", True, {
        "flagged": byzantine_result["flagged_count"]
    })

    # Step 4: State machine processing
    logger.log_state_transition("byzantine_detection", "state_processing", "detection_complete")
    state_result = process_transactions(
        data["transactions"],
        fee_rate=fee_rate
    )
    logger.log_verification("state_machine", state_result["failed_count"] == 0, {
        "processed": state_result["processed_count"],
        "failed": state_result["failed_count"],
    })

    # Step 5: Balance reconciliation
    logger.log_state_transition("state_processing", "reconciliation", "state_complete")
    reconciliation = reconcile_balances(
        data["transactions"],
        state_result["final_balances"],
        initial_balance=initial_balance,
        fee_rate=fee_rate
    )
    logger.log_verification("reconciliation", reconciliation["reconciled"], {
        "discrepancies": reconciliation["discrepancy_count"]
    })

    logger.log_state_transition("reconciliation", "complete", "reconciliation_done")
    audit_summary = logger.get_audit_summary()

    report = {
        "merkle_roots": merkle_roots,
        "quorum_results": {
            str(k): v for k, v in quorum_results.items()
        },
        "quorum_summary": quorum_summary,
        "byzantine_detection": {
            "flagged_validators": byzantine_result["flagged_validators"],
            "flagged_count": byzantine_result["flagged_count"],
        },
        "state_machine": {
            "final_balances": state_result["final_balances"],
            "total_fees": state_result["total_fees"],
            "state_hash": state_result["state_hash"],
            "processed_count": state_result["processed_count"],
            "failed_count": state_result["failed_count"],
        },
        "reconciliation": {
            "reconciled": reconciliation["reconciled"],
            "fingerprint_root": reconciliation["fingerprint_root"],
            "double_spend_count": reconciliation["double_spend_count"],
            "discrepancy_count": reconciliation["discrepancy_count"],
        },
        "audit_trail": audit_summary,
    }

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "audit_report.json")
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    report = run_pipeline()
    print(f"Pipeline complete. Processed {report['state_machine']['processed_count']} transactions.")
    print(f"Merkle batches: {len(report['merkle_roots'])}")
    print(f"Quorum rounds met: {report['quorum_summary']['quorum_met_count']}/{report['quorum_summary']['total_rounds']}")
    print(f"Byzantine validators: {report['byzantine_detection']['flagged_count']}")
    status = "PASS" if report['reconciliation']['reconciled'] else "FAIL"
    print(f"Reconciliation: {status}")
