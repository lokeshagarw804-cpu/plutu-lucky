# PLUTU-LUCKY-CANARY
"""Main pipeline for the distributed consensus ledger verification system."""
import json
import os
import configparser

from runtime.merkle_engine import compute_batch_roots, compute_global_root
from runtime.quorum_verifier import verify_all_rounds
from runtime.byzantine_detector import classify_validators
from runtime.state_machine import process_transactions, compute_state_hash
from runtime.balance_reconciler import detect_double_spends


def load_config():
    """Load configuration from config.ini."""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), "config.ini")
    config.read(config_path)
    return config


def load_data():
    """Load all data files."""
    data_dir = os.path.join(os.path.dirname(__file__), "data")

    with open(os.path.join(data_dir, "transactions.json")) as f:
        transactions = json.load(f)

    with open(os.path.join(data_dir, "validators.json")) as f:
        validators = json.load(f)

    with open(os.path.join(data_dir, "voting_records.json")) as f:
        voting_records = json.load(f)

    return transactions, validators, voting_records


def run_pipeline():
    """Execute the full verification pipeline."""
    config = load_config()

    # Extract configuration
    fee_rate = float(config["ledger"]["fee_rate"])
    initial_balance = int(config["ledger"]["initial_balance"])
    batch_size = int(config["merkle"]["batch_size"])
    output_path = config["audit"]["output_path"]

    # Load data
    transactions, validators, voting_records = load_data()

    # Step 1: Compute Merkle root
    batch_roots = compute_batch_roots(transactions, batch_size)
    merkle_root = compute_global_root(batch_roots)

    # Step 2: Verify consensus quorum
    quorum_results = verify_all_rounds(voting_records, validators)

    # Step 3: Detect Byzantine validators
    byzantine_list, honest_list = classify_validators(voting_records, validators)

    # Step 4: Process transactions and compute balances
    balances, total_fees = process_transactions(transactions, initial_balance, fee_rate)

    # Step 5: Compute state hash
    state_hash = compute_state_hash(balances, total_fees)

    # Step 6: Detect double-spends
    double_spends = detect_double_spends(transactions)

    # Build audit report
    audit_report = {
        "merkle_root": merkle_root,
        "total_transactions": len(transactions),
        "valid_rounds": quorum_results["valid_rounds"],
        "total_rounds": quorum_results["total_rounds"],
        "byzantine_validators": byzantine_list,
        "honest_validators": honest_list,
        "final_balances": balances,
        "total_fees_collected": total_fees,
        "double_spend_detected": double_spends,
        "quorum_failures": quorum_results["quorum_failures"],
        "state_hash": state_hash
    }

    # Write output
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(audit_report, f, indent=2)

    return audit_report


if __name__ == "__main__":
    report = run_pipeline()
    print(json.dumps(report, indent=2))
