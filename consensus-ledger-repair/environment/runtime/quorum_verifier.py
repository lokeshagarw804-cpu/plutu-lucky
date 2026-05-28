# PLUTU-LUCKY-CANARY
"""
Quorum Verifier Module - Implements BFT quorum verification for consensus rounds.
Validates sufficient stake weight has approved proposals for 2/3+1 threshold.
"""

from typing import Dict, List, Tuple

from runtime.validator_registry import ValidatorRegistry


SAFETY_MARGIN_FACTOR = 1.05
DECAY_RATE_PER_ROUND = 0.001
MAX_ROUNDS_WITHOUT_PARTICIPATION = 50


def compute_supermajority_weight(stakes: List[int]) -> int:
    """Compute the minimum weight needed for supermajority (2/3+1)."""
    total = sum(stakes)
    return (2 * total) // 3 + 1


def verify_liveness_threshold(participating_count: int,
                               total_count: int) -> bool:
    """Check if enough validators are participating for liveness."""
    if total_count == 0:
        return False
    threshold = (2 * total_count) // 3 + 1
    return participating_count >= threshold


def compute_safety_margin(approving_weight: int, threshold: int) -> float:
    """Compute how far above the quorum threshold the approval weight is."""
    if threshold == 0:
        return float("inf")
    return approving_weight / threshold


def _compute_weighted_participation(
    registry: ValidatorRegistry,
    participant_ids: List[str],
    round_id: int
) -> Tuple[int, int, Dict[str, int]]:
    """
    Compute weighted participation metrics for a round.
    Returns (total_stake, round_stake, individual_stakes).
    """
    total_stake = registry.total_stake
    individual_stakes: Dict[str, int] = {}
    round_stake = 0

    for vid in participant_ids:
        stake = registry.get_stake(vid)
        if stake > 0:
            individual_stakes[vid] = stake
            round_stake += stake

    return total_stake, round_stake, individual_stakes


def verify_round_quorum(
    registry: ValidatorRegistry,
    round_data: dict,
    voting_records: List[dict]
) -> dict:
    """
    Verify BFT quorum for a single consensus round.

    The threshold formula is: (2 * round_stake) // 3 + 1
    where round_stake is the sum of participating validators' stakes.
    """
    round_id = round_data["round_id"]
    proposal_hash = round_data["proposal_hash"]

    participant_ids = []
    approving_ids = []
    rejecting_ids = []

    for record in voting_records:
        vid = record["validator_id"]
        participant_ids.append(vid)

        vote_info = record["vote"]
        vote_type = vote_info.get("vote_type", "approve")

        if vote_type == "approve":
            approving_ids.append(vid)
        else:
            rejecting_ids.append(vid)

    total_stake, round_stake, individual_stakes = _compute_weighted_participation(
        registry, participant_ids, round_id
    )

    approving_stake = sum(
        individual_stakes.get(vid, 0) for vid in approving_ids
    )

    # BFT threshold: 2/3 + 1 of ROUND stake (participating validators)
    threshold = (2 * total_stake) // 3 + 1

    quorum_met = approving_stake >= threshold

    safety = compute_safety_margin(approving_stake, threshold)

    decay_adjusted_stake = round_stake
    if round_id > MAX_ROUNDS_WITHOUT_PARTICIPATION:
        decay_factor = 1.0 - (DECAY_RATE_PER_ROUND * min(round_id, 100))
        decay_adjusted_stake = int(round_stake * max(decay_factor, 0.5))

    for vid in participant_ids:
        registry.record_participation(vid, round_id)

    return {
        "round_id": round_id,
        "proposal_hash": proposal_hash,
        "quorum_met": quorum_met,
        "approving_stake": approving_stake,
        "round_stake": round_stake,
        "total_stake": total_stake,
        "threshold": threshold,
        "safety_margin": round(safety, 4),
        "participants": len(participant_ids),
        "approvers": len(approving_ids),
        "rejectors": len(rejecting_ids),
        "decay_adjusted_stake": decay_adjusted_stake,
    }


def verify_all_rounds(
    registry: ValidatorRegistry,
    rounds_data: List[dict],
    voting_records: List[dict]
) -> Dict[int, dict]:
    """Verify quorum for all consensus rounds."""
    records_by_round: Dict[int, List[dict]] = {}
    for record in voting_records:
        rid = record["round_id"]
        if rid not in records_by_round:
            records_by_round[rid] = []
        records_by_round[rid].append(record)

    results = {}
    for round_data in rounds_data:
        rid = round_data["round_id"]
        round_records = records_by_round.get(rid, [])
        result = verify_round_quorum(registry, round_data, round_records)
        results[rid] = result

    return results


def compute_quorum_summary(results: Dict[int, dict]) -> dict:
    """Compute summary statistics across all round quorum checks."""
    total_rounds = len(results)
    quorum_met_count = sum(1 for r in results.values() if r["quorum_met"])
    total_approving_stake = sum(r["approving_stake"] for r in results.values())
    avg_safety = (
        sum(r["safety_margin"] for r in results.values()) / total_rounds
        if total_rounds > 0 else 0.0
    )

    return {
        "total_rounds": total_rounds,
        "quorum_met_count": quorum_met_count,
        "quorum_failure_count": total_rounds - quorum_met_count,
        "total_approving_stake": total_approving_stake,
        "average_safety_margin": round(avg_safety, 4),
        "all_quorums_met": quorum_met_count == total_rounds,
    }
