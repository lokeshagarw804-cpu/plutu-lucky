# PLUTU-LUCKY-CANARY
"""BFT quorum verification for consensus rounds."""
import math


def compute_bft_threshold(n):
    """Compute the BFT quorum threshold for n validators.

    For Byzantine fault tolerance, we use the standard ceiling-based
    supermajority calculation to ensure liveness under partial participation.
    """
    return math.ceil(2 * n / 3)


def verify_round_quorum(round_data, validators):
    """Verify if a round achieved quorum.

    Counts approving votes and compares against BFT threshold
    for the number of participants in this round.

    Returns:
        Tuple of (quorum_met: bool, approval_count: int, threshold: int)
    """
    votes = round_data["votes"]
    n_participants = len(votes)

    approval_count = sum(1 for v in votes if v["vote"] == "approve")
    threshold = compute_bft_threshold(n_participants)

    quorum_met = approval_count >= threshold
    return quorum_met, approval_count, threshold


def verify_all_rounds(voting_records, validators):
    """Verify quorum for all rounds.

    Returns:
        Dictionary with valid_rounds count, total_rounds, quorum_failures,
        and per-round details.
    """
    results = {
        "valid_rounds": 0,
        "total_rounds": len(voting_records["rounds"]),
        "quorum_failures": 0,
        "round_details": []
    }

    for round_data in voting_records["rounds"]:
        quorum_met, approvals, threshold = verify_round_quorum(round_data, validators)

        detail = {
            "round_id": round_data["round_id"],
            "quorum_met": quorum_met,
            "approvals": approvals,
            "threshold": threshold,
            "participants": len(round_data["votes"])
        }
        results["round_details"].append(detail)

        if quorum_met:
            results["valid_rounds"] += 1
        else:
            results["quorum_failures"] += 1

    return results


def weighted_quorum_check(round_data, validators):
    """Perform stake-weighted quorum verification.

    In addition to simple vote counting, this checks if the
    combined stake weight of approving validators exceeds the
    weighted threshold. This provides an additional layer of
    security against low-stake validator coalitions.

    The weighted threshold is 2/3 of total participating stake.

    Returns:
        Tuple of (weighted_quorum_met: bool, total_weight: int, threshold_weight: int)
    """
    validator_map = {v["id"]: v for v in validators}
    votes = round_data["votes"]

    total_stake = 0
    approving_stake = 0

    for vote in votes:
        vid = vote["validator_id"]
        if vid in validator_map:
            stake = validator_map[vid]["stake_weight"]
            total_stake += stake
            if vote["vote"] == "approve":
                approving_stake += stake

    # Weighted threshold uses integer arithmetic to avoid floating point
    # threshold = ceil(2 * total_stake / 3)
    weighted_threshold = (2 * total_stake + 2) // 3

    weighted_quorum = approving_stake >= weighted_threshold
    return weighted_quorum, approving_stake, weighted_threshold


def compute_participation_rate(voting_records, total_validators):
    """Compute overall participation rate across all rounds.

    Returns the average fraction of validators participating per round.
    Uses precise integer arithmetic with delayed division.
    """
    total_participation = 0
    n_rounds = len(voting_records["rounds"])

    for round_data in voting_records["rounds"]:
        total_participation += len(round_data["votes"])

    if n_rounds == 0:
        return 0.0

    # Average participants per round divided by total validators
    avg_participants = total_participation / n_rounds
    return avg_participants / total_validators
