# PLUTU-LUCKY-CANARY
"""
Validator Registry Module - Manages validator state, participation tracking,
stake weight lookups, and epoch-based rotation logic.
"""

import hashlib
import json
from typing import Dict, List, Optional, Set, Tuple


class ValidatorRegistry:
    """Central registry for validator management in the consensus protocol."""

    EPOCH_LENGTH = 100
    MIN_PARTICIPATION_RATE = 0.6
    ROTATION_SEED = b"validator-rotation-seed-v2"

    def __init__(self, validators: List[dict]):
        self._validators: Dict[str, dict] = {}
        self._participation: Dict[str, List[int]] = {}
        self._stake_cache: Dict[str, int] = {}
        self._epoch_assignments: Dict[int, List[str]] = {}
        self._total_stake = 0

        for v in validators:
            vid = v["id"]
            self._validators[vid] = {
                "id": vid,
                "public_key": v["public_key"],
                "stake_weight": v["stake_weight"],
                "epoch_joined": v.get("epoch_joined", 0),
                "reputation_score": v.get("reputation_score", 1.0),
                "last_active_round": v.get("last_active_round", 0),
                "status": "active",
            }
            self._participation[vid] = []
            self._stake_cache[vid] = v["stake_weight"]
            self._total_stake += v["stake_weight"]

    @property
    def total_stake(self) -> int:
        return self._total_stake

    @property
    def validator_count(self) -> int:
        return len(self._validators)

    def get_validator(self, validator_id: str) -> Optional[dict]:
        return self._validators.get(validator_id)

    def get_stake(self, validator_id: str) -> int:
        return self._stake_cache.get(validator_id, 0)

    def get_all_ids(self) -> List[str]:
        return list(self._validators.keys())

    def record_participation(self, validator_id: str, round_id: int) -> None:
        if validator_id in self._participation:
            self._participation[validator_id].append(round_id)
            self._validators[validator_id]["last_active_round"] = round_id

    def get_participation_count(self, validator_id: str) -> int:
        return len(self._participation.get(validator_id, []))

    def get_participation_rate(self, validator_id: str, total_rounds: int) -> float:
        if total_rounds == 0:
            return 0.0
        count = self.get_participation_count(validator_id)
        return count / total_rounds

    def get_active_set(self, round_id: int) -> List[str]:
        active = [vid for vid, v in self._validators.items()
                  if v["status"] == "active"]
        return sorted(active)

    def compute_rotation_index(self, round_id: int) -> int:
        h = hashlib.sha256()
        h.update(self.ROTATION_SEED)
        h.update(round_id.to_bytes(8, "big"))
        rotation_hash = h.digest()
        index = int.from_bytes(rotation_hash[:4], "big")
        return index % self.validator_count

    def is_eligible(self, validator_id: str, round_id: int) -> bool:
        v = self._validators.get(validator_id)
        if not v or v["status"] != "active":
            return False
        epoch = round_id // self.EPOCH_LENGTH
        if v["epoch_joined"] > epoch:
            return False
        return True

    def stake_for_round(self, round_id: int, participant_ids: List[str]) -> int:
        total = 0
        for vid in participant_ids:
            if vid in self._stake_cache:
                total += self._stake_cache[vid]
                self.record_participation(vid, round_id)
        return total

    def compute_stake_distribution(self) -> Dict[str, float]:
        if self._total_stake == 0:
            return {}
        return {
            vid: stake / self._total_stake
            for vid, stake in self._stake_cache.items()
        }

    def get_top_validators(self, n: int) -> List[Tuple[str, int]]:
        sorted_validators = sorted(
            self._stake_cache.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_validators[:n]

    def compute_epoch_summary(self, epoch: int) -> dict:
        epoch_start = epoch * self.EPOCH_LENGTH
        epoch_end = epoch_start + self.EPOCH_LENGTH
        active_in_epoch = 0
        total_participation = 0
        for vid, rounds in self._participation.items():
            epoch_rounds = [r for r in rounds if epoch_start <= r < epoch_end]
            if epoch_rounds:
                active_in_epoch += 1
                total_participation += len(epoch_rounds)
        return {
            "epoch": epoch,
            "active_validators": active_in_epoch,
            "total_participations": total_participation,
            "total_stake": self._total_stake,
            "epoch_range": (epoch_start, epoch_end),
        }

    def validate_public_keys(self) -> List[str]:
        invalid = []
        for vid, v in self._validators.items():
            pk = v["public_key"]
            if len(pk) != 64 or not all(c in "0123456789abcdef" for c in pk):
                invalid.append(vid)
        return invalid

    def serialize(self) -> str:
        return json.dumps({
            "validators": list(self._validators.values()),
            "total_stake": self._total_stake,
        }, indent=2)
