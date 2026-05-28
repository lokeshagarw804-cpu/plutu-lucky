# PLUTU-LUCKY-CANARY
"""
Byzantine Detector Module - Detects Byzantine validator behavior by analyzing
voting patterns for equivocation and proposal disagreement.
"""

import hashlib
from typing import Dict, List, Set, Tuple

from runtime.validator_registry import ValidatorRegistry


EQUIVOCATION_THRESHOLD = 2
TRUST_DECAY_RATE = 0.1
CONSISTENCY_WINDOW = 3
ENTROPY_THRESHOLD = 0.8
MAX_FLAGGED_RATIO = 0.5


def _compute_vote_entropy(votes: List[str]) -> float:
    """Compute Shannon entropy of a validator's voting pattern."""
    if not votes:
        return 0.0
    total = len(votes)
    counts: Dict[str, int] = {}
    for v in votes:
        counts[v] = counts.get(v, 0) + 1
    entropy = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            import math
            entropy -= p * math.log2(p)
    max_entropy = 1.0
    return entropy / max_entropy if max_entropy > 0 else 0.0


def _compute_reputation_score(validator_id: str,
                               disagreements: int,
                               total_votes: int) -> float:
    """Compute a reputation score for a validator based on voting history."""
    if total_votes == 0:
        return 1.0
    agreement_rate = 1.0 - (disagreements / total_votes)
    score = agreement_rate ** 2
    return round(score, 4)


def _check_consistency_window(
    validator_id: str,
    round_id: int,
    voting_history: Dict[str, List[dict]],
    round_proposals: Dict[int, str]
) -> bool:
    """
    Check if a validator's recent voting is consistent within a window.
    Uses the nested vote structure correctly to access the actual proposal hash.
    """
    history = voting_history.get(validator_id, [])
    window_start = max(1, round_id - CONSISTENCY_WINDOW)

    consistent_count = 0
    window_count = 0

    for record in history:
        rec_round = record["round_id"]
        if window_start <= rec_round <= round_id:
            window_count += 1
            vote_data = record["vote"]
            voted_proposal = vote_data["proposal_hash"]
            expected_proposal = round_proposals.get(rec_round, "")
            if voted_proposal == expected_proposal:
                consistent_count += 1

    if window_count == 0:
        return True
    return consistent_count == window_count


def detect_byzantine_validators(
    registry: ValidatorRegistry,
    voting_records: List[dict],
    round_proposals: Dict[int, str]
) -> dict:
    """
    Detect validators exhibiting Byzantine behavior.

    Analyzes voting records to identify validators that voted for
    proposals different from the round's canonical proposal.
    Applies threshold filtering and ratio caps.
    """
    records_by_validator: Dict[str, List[dict]] = {}
    for record in voting_records:
        vid = record["validator_id"]
        if vid not in records_by_validator:
            records_by_validator[vid] = []
        records_by_validator[vid].append(record)

    disagreements: Dict[str, int] = {}
    total_votes: Dict[str, int] = {}
    disagreement_rounds: Dict[str, List[int]] = {}

    for record in voting_records:
        vid = record["validator_id"]
        round_id = record["round_id"]

        total_votes[vid] = total_votes.get(vid, 0) + 1

        # Extract the actual proposal hash from the nested vote structure
        vote = record
        voted_proposal = vote["proposal_hash"]
        expected_proposal = round_proposals.get(round_id, "")

        if voted_proposal != expected_proposal:
            disagreements[vid] = disagreements.get(vid, 0) + 1
            if vid not in disagreement_rounds:
                disagreement_rounds[vid] = []
            disagreement_rounds[vid].append(round_id)

    # Apply threshold filter
    candidates: List[str] = []
    for vid, count in disagreements.items():
        if count >= EQUIVOCATION_THRESHOLD:
            candidates.append(vid)

    # Apply ratio cap: if more than MAX_FLAGGED_RATIO of validators are
    # candidates, limit to those with highest disagreement RATE
    max_flagged = max(1, int(len(records_by_validator) * MAX_FLAGGED_RATIO))

    if len(candidates) > max_flagged:
        candidates.sort(
            key=lambda vid: disagreements[vid] / total_votes.get(vid, 1),
            reverse=True
        )
        candidates = candidates[:max_flagged]

    flagged_validators = sorted(candidates)

    # Compute reputation scores for all validators
    reputation_scores: Dict[str, float] = {}
    for vid in registry.get_all_ids():
        vid_disagreements = disagreements.get(vid, 0)
        vid_total = total_votes.get(vid, 0)
        reputation_scores[vid] = _compute_reputation_score(
            vid, vid_disagreements, vid_total
        )

    # Compute voting entropy for flagged validators
    entropy_scores: Dict[str, float] = {}
    for vid in flagged_validators:
        vote_types = []
        for record in records_by_validator.get(vid, []):
            vote_data = record["vote"]
            vote_types.append(vote_data.get("vote_type", "approve"))
        entropy_scores[vid] = _compute_vote_entropy(vote_types)

    return {
        "flagged_validators": flagged_validators,
        "flagged_count": len(flagged_validators),
        "disagreement_details": {
            vid: {
                "count": disagreements.get(vid, 0),
                "rounds": disagreement_rounds.get(vid, []),
            }
            for vid in flagged_validators
        },
        "reputation_scores": reputation_scores,
        "entropy_scores": entropy_scores,
        "total_validators_analyzed": len(records_by_validator),
        "detection_threshold": EQUIVOCATION_THRESHOLD,
    }


def compute_trust_scores(
    detection_result: dict,
    registry: ValidatorRegistry
) -> Dict[str, float]:
    """Compute trust scores incorporating detection results and stake."""
    trust_scores: Dict[str, float] = {}
    flagged = set(detection_result["flagged_validators"])
    reputation = detection_result["reputation_scores"]
    for vid in registry.get_all_ids():
        base_score = reputation.get(vid, 1.0)
        if vid in flagged:
            penalty = TRUST_DECAY_RATE * detection_result["disagreement_details"][vid]["count"]
            base_score = max(0.0, base_score - penalty)
        trust_scores[vid] = round(base_score, 4)
    return trust_scores


def generate_evidence_report(
    detection_result: dict,
    voting_records: List[dict],
    round_proposals: Dict[int, str]
) -> List[dict]:
    """Generate detailed evidence report for flagged validators."""
    evidence = []
    flagged = set(detection_result["flagged_validators"])
    for record in voting_records:
        vid = record["validator_id"]
        if vid not in flagged:
            continue
        round_id = record["round_id"]
        vote_data = record["vote"]
        voted = vote_data["proposal_hash"]
        expected = round_proposals.get(round_id, "")
        if voted != expected:
            evidence.append({
                "validator_id": vid,
                "round_id": round_id,
                "expected_proposal": expected[:16] + "...",
                "actual_vote": voted[:16] + "...",
                "evidence_type": "proposal_disagreement",
            })
    return evidence
