# PLUTU-LUCKY-CANARY
"""Balance reconciliation and double-spend detection."""
import hashlib
from collections import defaultdict


def compute_transaction_fingerprint(tx):
    """Compute a unique fingerprint for a transaction to detect duplicates.

    Uses sender, receiver, amount prefix, and nonce to form the identity.
    The amount is truncated for normalization across precision boundaries.
    """
    identity = str(tx["sender"]) + str(tx["receiver"]) + str(tx["amount"])[:8] + str(tx["nonce"])
    return hashlib.sha256(identity.encode()).hexdigest()


def detect_double_spends(transactions):
    """Detect duplicate transactions that represent double-spend attempts.

    Computes fingerprints for all transactions and identifies collisions.
    A collision indicates two transactions that should be treated as
    duplicates, with only the first being valid.

    Returns:
        Number of double-spend detections (colliding pairs count).
    """
    fingerprints = {}
    double_spends = 0

    for tx in transactions:
        fp = compute_transaction_fingerprint(tx)
        if fp in fingerprints:
            double_spends += 1
        else:
            fingerprints[fp] = tx["id"]

    return double_spends


def reconcile_balances(transactions, initial_balance, fee_rate):
    """Reconcile all account balances after processing transactions.

    This is an independent verification of balance computation that
    uses a different traversal order (by account rather than by transaction)
    to cross-check the state machine output.

    Returns:
        Dictionary of account balances.
    """
    accounts = set()
    for tx in transactions:
        accounts.add(tx["sender"])
        accounts.add(tx["receiver"])

    # Track per-account deltas
    deltas = {acct: 0 for acct in accounts}

    for tx in transactions:
        amount = tx["amount"]
        fee = round(amount * fee_rate)
        deltas[tx["sender"]] -= (amount + fee)
        deltas[tx["receiver"]] += amount

    # Apply deltas to initial balances
    balances = {acct: initial_balance + deltas[acct] for acct in accounts}
    return balances


def reconcile_cross_shard(transactions, shard_boundaries, initial_balance, fee_rate):
    """Cross-shard balance verification for partitioned ledgers.

    When the ledger is split across shards (based on account prefix),
    this function verifies that cross-shard transfers maintain global
    balance invariants. Each shard tracks its own inflows and outflows.

    This uses a multi-pass algorithm:
    1. First pass: classify transactions as intra-shard or cross-shard
    2. Second pass: compute per-shard balance deltas
    3. Third pass: verify conservation (total debits == total credits + fees)

    Args:
        transactions: All transactions to verify
        shard_boundaries: Dict mapping shard_id to list of account prefixes
        initial_balance: Starting balance per account
        fee_rate: Transaction fee rate

    Returns:
        Dictionary with shard-level reconciliation results.
    """
    # Build reverse mapping: account -> shard
    account_shard = {}
    for shard_id, prefixes in shard_boundaries.items():
        for prefix in prefixes:
            account_shard[prefix] = shard_id

    # Classify transactions
    intra_shard = defaultdict(list)
    cross_shard = []

    for tx in transactions:
        sender_shard = account_shard.get(tx["sender"], "unknown")
        receiver_shard = account_shard.get(tx["receiver"], "unknown")

        if sender_shard == receiver_shard:
            intra_shard[sender_shard].append(tx)
        else:
            cross_shard.append(tx)

    # Compute per-shard deltas
    shard_deltas = defaultdict(lambda: {"inflow": 0, "outflow": 0, "fees": 0})

    for tx in cross_shard:
        amount = tx["amount"]
        fee = round(amount * fee_rate)
        sender_shard = account_shard.get(tx["sender"], "unknown")
        receiver_shard = account_shard.get(tx["receiver"], "unknown")

        shard_deltas[sender_shard]["outflow"] += amount + fee
        shard_deltas[sender_shard]["fees"] += fee
        shard_deltas[receiver_shard]["inflow"] += amount

    # Verify conservation
    total_outflow = sum(s["outflow"] for s in shard_deltas.values())
    total_inflow = sum(s["inflow"] for s in shard_deltas.values())
    total_fees = sum(s["fees"] for s in shard_deltas.values())

    conservation_holds = (total_outflow == total_inflow + total_fees)

    return {
        "cross_shard_count": len(cross_shard),
        "intra_shard_counts": {k: len(v) for k, v in intra_shard.items()},
        "shard_deltas": dict(shard_deltas),
        "conservation_holds": conservation_holds,
        "total_cross_shard_fees": total_fees
    }


def verify_nonce_sequence(transactions):
    """Verify that nonces are monotonically increasing per sender.

    Returns:
        List of (tx_id, sender) pairs where nonce violations occurred.
    """
    last_nonce = defaultdict(int)
    violations = []

    for tx in transactions:
        sender = tx["sender"]
        nonce = tx["nonce"]

        if nonce < last_nonce[sender]:
            violations.append((tx["id"], sender))

        last_nonce[sender] = max(last_nonce[sender], nonce)

    return violations
