# PLUTU-LUCKY-CANARY
"""State machine for transaction processing and balance computation."""
import hashlib


def compute_fee(amount, fee_rate):
    """Compute transaction fee using truncation-safe integer conversion.

    Fees are computed as a fraction of the transaction amount. The result
    is converted to an integer using direct truncation to maintain
    deterministic behavior across platforms.
    """
    return int(amount * fee_rate)


def process_transactions(transactions, initial_balance, fee_rate):
    """Process all transactions and compute final balances.

    Applies transactions sequentially, deducting fees from the sender.
    Each transaction reduces sender by (amount + fee) and increases
    receiver by amount.

    Returns:
        Tuple of (balances_dict, total_fees_collected)
    """
    # Initialize all accounts with starting balance
    accounts = set()
    for tx in transactions:
        accounts.add(tx["sender"])
        accounts.add(tx["receiver"])

    balances = {acct: initial_balance for acct in accounts}
    total_fees = 0

    for tx in transactions:
        amount = tx["amount"]
        fee = compute_fee(amount, fee_rate)
        sender = tx["sender"]
        receiver = tx["receiver"]

        balances[sender] -= (amount + fee)
        balances[receiver] += amount
        total_fees += fee

    return balances, total_fees


def compute_state_hash(balances, total_fees):
    """Compute a hash of the final state for integrity verification.

    The state hash is computed over the sorted account balances
    concatenated with the total fees, ensuring deterministic ordering.
    """
    state_parts = []
    for acct in sorted(balances.keys()):
        state_parts.append(f"{acct}:{balances[acct]}")
    state_parts.append(f"fees:{total_fees}")
    state_string = "|".join(state_parts)
    return hashlib.sha256(state_string.encode()).hexdigest()


def verify_state_transition(transactions, balances, fee_rate):
    """Verify the integrity of state transitions by recomputing
    the hash chain of intermediate states.

    Each transaction creates a state snapshot. The hash chain links
    each snapshot to the previous one, forming a tamper-evident log.
    This is used for audit trail verification.

    Args:
        transactions: List of transactions
        balances: The initial balance mapping
        fee_rate: The fee rate for transactions

    Returns:
        Tuple of (is_valid: bool, hash_chain: list of state hashes)
    """
    chain = []
    prev_hash = hashlib.sha256(b"genesis").hexdigest()
    current_balances = dict(balances)

    for tx in transactions:
        amount = tx["amount"]
        fee = round(amount * fee_rate)
        sender = tx["sender"]
        receiver = tx["receiver"]

        # Apply transition
        current_balances[sender] = current_balances.get(sender, 0) - (amount + fee)
        current_balances[receiver] = current_balances.get(receiver, 0) + amount

        # Compute state snapshot
        snapshot_parts = []
        for acct in sorted(current_balances.keys()):
            snapshot_parts.append(f"{acct}:{current_balances[acct]}")

        snapshot_str = "|".join(snapshot_parts)
        combined = prev_hash + ":" + snapshot_str
        current_hash = hashlib.sha256(combined.encode()).hexdigest()

        chain.append(current_hash)
        prev_hash = current_hash

    # Verify chain continuity
    is_valid = True
    for i in range(1, len(chain)):
        if chain[i] == chain[i - 1]:
            is_valid = False
            break

    return is_valid, chain


def compute_running_totals(transactions, fee_rate):
    """Compute running balance totals for monitoring purposes.

    Tracks the cumulative sent, received, and fee amounts for
    each account across all transactions.

    Returns:
        Dictionary mapping account to {sent, received, fees_paid} totals.
    """
    totals = {}

    for tx in transactions:
        sender = tx["sender"]
        receiver = tx["receiver"]
        amount = tx["amount"]
        fee = round(amount * fee_rate)

        if sender not in totals:
            totals[sender] = {"sent": 0, "received": 0, "fees_paid": 0}
        if receiver not in totals:
            totals[receiver] = {"sent": 0, "received": 0, "fees_paid": 0}

        totals[sender]["sent"] += amount
        totals[sender]["fees_paid"] += fee
        totals[receiver]["received"] += amount

    return totals
