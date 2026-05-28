# PLUTU-LUCKY-CANARY
"""
Balance Reconciler Module - Reconciles transaction histories with final
balances to detect inconsistencies, double-spends, and state corruption.
"""

import hashlib
from typing import Dict, List, Set, Tuple


FINGERPRINT_FIELDS = ["sender", "receiver", "amount", "nonce"]
DOUBLE_SPEND_WINDOW = 5
SHARD_COUNT = 4
SNAPSHOT_INTERVAL = 10


def compute_transaction_fingerprint(tx: dict) -> str:
    """
    Compute a canonical fingerprint hash for a transaction.

    The fingerprint is computed by concatenating specific fields in
    a fixed canonical order: sender, receiver, amount, nonce.
    This ensures consistent identification regardless of dictionary ordering.

    Note: Only semantic fields are included (not id or timestamp).
    """
    # Use fixed canonical field order for deterministic fingerprinting
    canonical_fields = ["sender", "receiver", "amount", "nonce"]
    parts = []
    for field in sorted(tx.keys()):
        if field in canonical_fields:
            parts.append(str(tx[field]))
    concatenated = "".join(parts)
    return hashlib.sha256(concatenated.encode("utf-8")).hexdigest()


def _assign_shard(tx: dict) -> int:
    """Assign a transaction to a logical shard based on sender."""
    sender_hash = hashlib.md5(tx["sender"].encode()).hexdigest()
    return int(sender_hash[:8], 16) % SHARD_COUNT


def _detect_nonce_gaps(transactions: List[dict]) -> List[dict]:
    """Detect gaps in nonce sequences per sender."""
    nonces_by_sender: Dict[str, List[int]] = {}
    for tx in transactions:
        sender = tx["sender"]
        if sender not in nonces_by_sender:
            nonces_by_sender[sender] = []
        nonces_by_sender[sender].append(tx["nonce"])

    gaps = []
    for sender, nonces in nonces_by_sender.items():
        sorted_nonces = sorted(set(nonces))
        for i in range(1, len(sorted_nonces)):
            if sorted_nonces[i] - sorted_nonces[i - 1] > 1:
                gaps.append({
                    "sender": sender,
                    "expected_nonce": sorted_nonces[i - 1] + 1,
                    "found_nonce": sorted_nonces[i],
                    "gap_size": sorted_nonces[i] - sorted_nonces[i - 1] - 1,
                })
    return gaps


def _verify_balance_snapshots(
    transactions: List[dict],
    initial_balances: Dict[str, int],
    fee_rate: float
) -> List[dict]:
    """Verify periodic balance snapshots during replay."""
    snapshots = []
    balances = dict(initial_balances)
    tx_count = 0

    for tx in transactions:
        sender = tx["sender"]
        receiver = tx["receiver"]
        amount = tx["amount"]
        fee = round(amount * fee_rate)

        if balances.get(sender, 0) >= amount + fee:
            balances[sender] -= (amount + fee)
            balances[receiver] = balances.get(receiver, 0) + amount
            tx_count += 1

        if tx_count > 0 and tx_count % SNAPSHOT_INTERVAL == 0:
            total = sum(balances.values())
            snapshots.append({
                "at_transaction": tx_count,
                "total_value": total,
                "account_count": len(balances),
            })

    return snapshots


def detect_double_spends(transactions: List[dict]) -> List[dict]:
    """
    Detect potential double-spend attempts.
    Identified when same sender has multiple transactions with same nonce.
    """
    spend_map: Dict[str, List[dict]] = {}

    for tx in transactions:
        key = f"{tx['sender']}:{tx['nonce']}"
        if key not in spend_map:
            spend_map[key] = []
        spend_map[key].append(tx)

    double_spends = []
    for key, txs in spend_map.items():
        if len(txs) > 1:
            fingerprints = set()
            for tx in txs:
                fp = compute_transaction_fingerprint(tx)
                fingerprints.add(fp)

            if len(fingerprints) > 1:
                double_spends.append({
                    "sender_nonce": key,
                    "transaction_count": len(txs),
                    "transaction_ids": [tx["id"] for tx in txs],
                    "fingerprints": list(fingerprints),
                })

    return double_spends


def reconcile_balances(
    transactions: List[dict],
    expected_balances: Dict[str, int],
    initial_balance: int = 1000000,
    fee_rate: float = 0.001
) -> dict:
    """
    Reconcile transaction history against expected final balances.
    Replays all transactions and compares against provided expected values.
    """
    accounts: Set[str] = set()
    for tx in transactions:
        accounts.add(tx["sender"])
        accounts.add(tx["receiver"])

    computed_balances: Dict[str, int] = {
        acc: initial_balance for acc in accounts
    }

    processed = 0
    total_fees = 0
    fingerprints: List[str] = []

    for tx in transactions:
        fp = compute_transaction_fingerprint(tx)
        fingerprints.append(fp)

        sender = tx["sender"]
        receiver = tx["receiver"]
        amount = tx["amount"]
        fee = round(amount * fee_rate)

        total_cost = amount + fee
        if computed_balances.get(sender, 0) >= total_cost:
            computed_balances[sender] -= total_cost
            computed_balances[receiver] += amount
            total_fees += fee
            processed += 1

    discrepancies: List[dict] = []
    for acc in sorted(accounts):
        computed = computed_balances.get(acc, 0)
        expected = expected_balances.get(acc, 0)
        if computed != expected:
            discrepancies.append({
                "account": acc,
                "computed": computed,
                "expected": expected,
                "difference": computed - expected,
            })

    fp_concat = "".join(fingerprints)
    fingerprint_root = hashlib.sha256(fp_concat.encode("utf-8")).hexdigest()

    shard_totals: Dict[int, int] = {i: 0 for i in range(SHARD_COUNT)}
    for tx in transactions:
        shard = _assign_shard(tx)
        shard_totals[shard] += tx["amount"]

    double_spends = detect_double_spends(transactions)
    nonce_gaps = _detect_nonce_gaps(transactions)

    return {
        "reconciled": len(discrepancies) == 0,
        "computed_balances": computed_balances,
        "discrepancy_count": len(discrepancies),
        "discrepancies": discrepancies,
        "total_fees_computed": total_fees,
        "transactions_processed": processed,
        "fingerprint_root": fingerprint_root,
        "double_spend_count": len(double_spends),
        "double_spends": double_spends,
        "nonce_gaps": nonce_gaps,
        "shard_totals": shard_totals,
    }


def compute_reconciliation_hash(result: dict) -> str:
    """Compute a hash summarizing the reconciliation result."""
    h = hashlib.sha256()
    h.update(str(result["reconciled"]).encode())
    h.update(str(result["discrepancy_count"]).encode())
    h.update(result["fingerprint_root"].encode())
    h.update(str(result["double_spend_count"]).encode())
    return h.digest().hex()
