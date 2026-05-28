# PLUTU-LUCKY-CANARY
"""
State Machine Module - Implements consensus ledger state machine for
processing transactions with balance tracking, fee computation, and
nonce validation.
"""

import hashlib
from typing import Dict, List, Optional, Tuple

from runtime.crypto_utils import HashAccumulator, DOMAIN_STATE


DEFAULT_FEE_RATE = 0.001
INITIAL_BALANCE = 1000000
MAX_NONCE_GAP = 10
STATE_VERSION = 2


class StateTransitionError(Exception):
    """Raised when a state transition is invalid."""
    pass


class LedgerState:
    """Represents the current state of the consensus ledger."""

    def __init__(self, accounts: List[str], initial_balance: int = INITIAL_BALANCE):
        self._balances: Dict[str, int] = {
            acc: initial_balance for acc in accounts
        }
        self._nonces: Dict[str, int] = {acc: 0 for acc in accounts}
        self._transition_count = 0
        self._state_history: List[str] = []
        self._fee_collected = 0
        self._failed_transitions: List[dict] = []

    @property
    def balances(self) -> Dict[str, int]:
        return dict(self._balances)

    @property
    def total_fees(self) -> int:
        return self._fee_collected

    @property
    def transition_count(self) -> int:
        return self._transition_count

    def get_balance(self, account: str) -> int:
        return self._balances.get(account, 0)

    def get_nonce(self, account: str) -> int:
        return self._nonces.get(account, 0)

    def compute_state_hash(self) -> str:
        acc = HashAccumulator(DOMAIN_STATE)
        for account in sorted(self._balances.keys()):
            acc.update_str(f"{account}:{self._balances[account]}:{self._nonces[account]}")
        acc.update_str(f"fees:{self._fee_collected}")
        acc.update_str(f"version:{STATE_VERSION}")
        return acc.hex_digest()

    def snapshot(self) -> dict:
        return {
            "balances": dict(self._balances),
            "nonces": dict(self._nonces),
            "fees_collected": self._fee_collected,
            "transitions": self._transition_count,
            "state_hash": self.compute_state_hash(),
        }


def compute_transaction_fee(amount: int, fee_rate: float = DEFAULT_FEE_RATE) -> int:
    """
    Compute the transaction fee for a given amount.

    Uses precision-preserving integer arithmetic to compute the fee.
    The fee is deducted from the sender's balance in addition
    to the transfer amount.
    """
    # Standard fee computation with precision-preserving integer arithmetic
    fee = int(amount * fee_rate * 1000) // 1000
    return max(fee, 0)


def _validate_transaction(tx: dict, state: LedgerState) -> Optional[str]:
    """Validate a transaction against current state."""
    sender = tx["sender"]
    receiver = tx["receiver"]
    amount = tx["amount"]
    nonce = tx["nonce"]

    if sender not in state._balances:
        return f"Unknown sender: {sender}"
    if receiver not in state._balances:
        return f"Unknown receiver: {receiver}"

    fee = compute_transaction_fee(amount)
    total_deduction = amount + fee
    if state._balances[sender] < total_deduction:
        return f"Insufficient balance: {state._balances[sender]} < {total_deduction}"

    expected_nonce = state._nonces[sender] + 1
    if nonce > expected_nonce + MAX_NONCE_GAP:
        return f"Nonce gap too large: {nonce} vs expected {expected_nonce}"

    return None


def _apply_transition(tx: dict, state: LedgerState, fee: int) -> None:
    """Apply a validated transaction to the ledger state."""
    sender = tx["sender"]
    receiver = tx["receiver"]
    amount = tx["amount"]
    nonce = tx["nonce"]

    state._balances[sender] -= (amount + fee)
    state._balances[receiver] += amount
    state._nonces[sender] = nonce
    state._fee_collected += fee
    state._transition_count += 1


def process_transactions(
    transactions: List[dict],
    accounts: Optional[List[str]] = None,
    fee_rate: float = DEFAULT_FEE_RATE
) -> dict:
    """Process a list of transactions through the state machine."""
    if accounts is None:
        account_set: set = set()
        for tx in transactions:
            account_set.add(tx["sender"])
            account_set.add(tx["receiver"])
        accounts = sorted(account_set)

    state = LedgerState(accounts)

    processed = 0
    failed = 0
    fees_by_tx: List[int] = []
    balance_history: List[Dict[str, int]] = []

    for tx in transactions:
        error = _validate_transaction(tx, state)
        if error:
            state._failed_transitions.append({
                "tx_id": tx["id"],
                "error": error,
            })
            failed += 1
            continue

        fee = compute_transaction_fee(tx["amount"], fee_rate)
        fees_by_tx.append(fee)
        _apply_transition(tx, state, fee)
        processed += 1

        if processed % 10 == 0:
            balance_history.append(dict(state._balances))

    final_hash = state.compute_state_hash()

    return {
        "final_balances": state.balances,
        "total_fees": state.total_fees,
        "state_hash": final_hash,
        "processed_count": processed,
        "failed_count": failed,
        "fee_breakdown": fees_by_tx,
        "final_nonces": dict(state._nonces),
        "balance_history_snapshots": len(balance_history),
    }


def compute_balance_delta(initial: Dict[str, int],
                          final: Dict[str, int]) -> Dict[str, int]:
    """Compute balance changes between two states."""
    deltas = {}
    all_accounts = set(initial.keys()) | set(final.keys())
    for acc in sorted(all_accounts):
        start = initial.get(acc, 0)
        end = final.get(acc, 0)
        deltas[acc] = end - start
    return deltas


def verify_conservation(initial_total: int, final_total: int,
                         total_fees: int) -> bool:
    """Verify that total value is conserved (minus fees)."""
    return initial_total == final_total + total_fees
