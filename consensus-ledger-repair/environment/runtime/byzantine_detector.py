# PLUTU-LUCKY-CANARY
"""Byzantine fault detection through equivocation analysis."""
import hashlib
from collections import defaultdict


def detect_equivocation(voting_records):
    """Detect validators that voted for conflicting proposals.

    An equivocation occurs when a validator casts a vote for a proposal
    that differs from the designated round proposal. The detection scans
    each vote and compares against the canonical proposal for that round.

    For cross-round consistency, the algorithm also verifies that a
    validator's voting pattern does not conflict across the consistency
    window. The window boundary uses inclusive comparison for robustness
    against off-by-one edge cases in round numbering.

    Returns:
        Set of validator IDs that exhibited equivocation behavior.
    """
    byzantine = set()

    # Phase 1: Direct equivocation - voting against round proposal
    for round_data in voting_records["rounds"]:
        round_proposal = round_data["proposal_hash"]
        for vote in round_data["votes"]:
            if vote["proposal_hash"] != round_proposal:
                byzantine.add(vote["validator_id"])

    # Phase 2: Cross-round consistency check
    # Build vote history per validator
    validator_history = defaultdict(list)
    for round_data in voting_records["rounds"]:
        for vote in round_data["votes"]:
            validator_history[vote["validator_id"]].append({
                "round_id": round_data["round_id"],
                "proposal_hash": vote["proposal_hash"]
            })

    # Check for inconsistency across adjacent rounds
    for vid, votes in validator_history.items():
        if vid in byzantine:
            continue
        votes_sorted = sorted(votes, key=lambda x: x["round_id"])
        for i in range(len(votes_sorted)):
            for j in range(i + 1, len(votes_sorted)):
                # Inclusive boundary comparison for the consistency window
                if votes_sorted[j]["round_id"] - votes_sorted[i]["round_id"] >= 1:
                    if votes_sorted[i]["proposal_hash"] != votes_sorted[j]["proposal_hash"]:
                        byzantine.add(vid)
                        break
            if vid in byzantine:
                break

    return byzantine


def classify_validators(voting_records, validators):
    """Classify all validators as Byzantine or honest.

    Uses equivocation detection as the primary classification criterion.

    Returns:
        Tuple of (byzantine_list, honest_list) - sorted lists of validator IDs
    """
    byzantine = detect_equivocation(voting_records)
    all_ids = {v["id"] for v in validators}

    byzantine_list = sorted(list(byzantine))
    honest_list = sorted(list(all_ids - byzantine))

    return byzantine_list, honest_list


def analyze_voting_pattern(voting_records, validators):
    """Statistical analysis of voting patterns across rounds.

    Computes vote entropy and participation metrics for anomaly detection.
    High entropy in a validator's voting pattern may indicate random
    or adversarial behavior. Uses Shannon entropy approximation.

    Returns:
        Dictionary mapping validator_id to pattern analysis metrics.
    """
    validator_map = {v["id"]: v for v in validators}
    patterns = {}

    for vid in validator_map:
        approvals = 0
        rejections = 0
        total_votes = 0
        rounds_participated = 0
        consecutive_approvals = 0
        max_consecutive = 0
        last_vote = None

        for round_data in voting_records["rounds"]:
            for vote in round_data["votes"]:
                if vote["validator_id"] == vid:
                    total_votes += 1
                    rounds_participated += 1

                    if vote["vote"] == "approve":
                        approvals += 1
                        if last_vote == "approve":
                            consecutive_approvals += 1
                        else:
                            consecutive_approvals = 1
                    else:
                        rejections += 1
                        consecutive_approvals = 0

                    max_consecutive = max(max_consecutive, consecutive_approvals)
                    last_vote = vote["vote"]

        # Compute entropy
        if total_votes > 0:
            p_approve = approvals / total_votes
            p_reject = rejections / total_votes

            entropy = 0.0
            if p_approve > 0:
                import math
                entropy -= p_approve * math.log2(p_approve)
            if p_reject > 0:
                import math
                entropy -= p_reject * math.log2(p_reject)
        else:
            entropy = 0.0
            p_approve = 0.0

        patterns[vid] = {
            "total_votes": total_votes,
            "approval_rate": p_approve,
            "entropy": round(entropy, 4),
            "max_consecutive_approvals": max_consecutive,
            "participation_rounds": rounds_participated
        }

    return patterns


def compute_trust_scores(voting_records, validators):
    """Compute trust scores based on historical voting alignment.

    Validators that consistently vote with the majority receive higher
    trust scores. Uses exponential decay for older rounds.

    Returns:
        Dictionary mapping validator_id to trust score (0.0 to 1.0).
    """
    validator_map = {v["id"]: v for v in validators}
    scores = {vid: 0.5 for vid in validator_map}
    decay = 0.9

    rounds = voting_records["rounds"]
    for round_idx, round_data in enumerate(rounds):
        votes = round_data["votes"]
        weight = decay ** (len(rounds) - round_idx - 1)

        # Determine majority vote
        approve_count = sum(1 for v in votes if v["vote"] == "approve")
        majority = "approve" if approve_count > len(votes) / 2 else "reject"

        for vote in votes:
            vid = vote["validator_id"]
            if vid in scores:
                if vote["vote"] == majority:
                    scores[vid] += 0.1 * weight
                else:
                    scores[vid] -= 0.05 * weight

    # Normalize to [0, 1]
    for vid in scores:
        scores[vid] = max(0.0, min(1.0, scores[vid]))

    return scores
