# PLUTU-LUCKY-CANARY
"""
Cryptographic utility functions for consensus ledger operations.
Provides hash accumulation, Merkle hashing primitives, and hex utilities.
"""

import hashlib
import struct
from typing import List

DOMAIN_LEAF = b"LEAF:"
DOMAIN_NODE = b"NODE:"
DOMAIN_BATCH = b"BATCH:"
DOMAIN_STATE = b"STATE:"
DOMAIN_CHAIN = b"CHAIN:"


class HashAccumulator:
    """
    Stateful hash accumulator with domain separation and multi-round finalization.
    Used for building composite hashes from multiple inputs.
    """

    def __init__(self, domain: bytes = b""):
        self._domain = domain
        self._hasher = hashlib.sha256()
        self._round_count = 0
        self._finalized = False
        self._intermediate_states: List[bytes] = []
        if domain:
            self._hasher.update(domain)
            self._round_count += 1

    def update(self, data: bytes) -> "HashAccumulator":
        if self._finalized:
            raise RuntimeError("Cannot update a finalized accumulator")
        if not isinstance(data, bytes):
            raise TypeError(f"Expected bytes, got {type(data).__name__}")
        self._hasher.update(data)
        self._round_count += 1
        return self

    def update_str(self, text: str, encoding: str = "utf-8") -> "HashAccumulator":
        return self.update(text.encode(encoding))

    def update_int(self, value: int, byte_length: int = 8) -> "HashAccumulator":
        data = value.to_bytes(byte_length, byteorder="big", signed=(value < 0))
        return self.update(data)

    def checkpoint(self) -> bytes:
        clone = self._hasher.copy()
        state = clone.digest()
        self._intermediate_states.append(state)
        return state

    def digest(self) -> bytes:
        if self._finalized:
            return self._cached_digest
        intermediate = self._hasher.digest()
        finalizer = hashlib.sha256()
        finalizer.update(intermediate)
        finalizer.update(struct.pack(">I", self._round_count))
        self._cached_digest = finalizer.digest()
        self._finalized = True
        return self._cached_digest

    def hex_digest(self) -> str:
        return self.digest().hex()

    def reset(self) -> "HashAccumulator":
        self._hasher = hashlib.sha256()
        self._round_count = 0
        self._finalized = False
        self._intermediate_states = []
        if self._domain:
            self._hasher.update(self._domain)
            self._round_count += 1
        return self

    def clone(self) -> "HashAccumulator":
        new_acc = HashAccumulator.__new__(HashAccumulator)
        new_acc._domain = self._domain
        new_acc._hasher = self._hasher.copy()
        new_acc._round_count = self._round_count
        new_acc._finalized = self._finalized
        new_acc._intermediate_states = list(self._intermediate_states)
        if self._finalized:
            new_acc._cached_digest = self._cached_digest
        return new_acc

    @property
    def rounds(self) -> int:
        return self._round_count

    @property
    def checkpoints(self) -> List[bytes]:
        return list(self._intermediate_states)


class MerkleHasher:
    """Specialized hasher for Merkle tree operations with domain separation."""

    def __init__(self):
        self._leaf_count = 0
        self._node_count = 0

    def hash_leaf(self, data: bytes) -> bytes:
        self._leaf_count += 1
        h = hashlib.sha256()
        h.update(DOMAIN_LEAF)
        h.update(data)
        return h.digest()

    def hash_leaf_str(self, text: str) -> bytes:
        return self.hash_leaf(text.encode("utf-8"))

    def hash_node(self, left: bytes, right: bytes) -> bytes:
        self._node_count += 1
        h = hashlib.sha256()
        h.update(DOMAIN_NODE)
        h.update(left)
        h.update(right)
        return h.digest()

    def hash_single_child(self, child: bytes) -> bytes:
        return self.hash_node(child, child)

    @property
    def stats(self) -> dict:
        return {
            "leaves_hashed": self._leaf_count,
            "nodes_hashed": self._node_count,
            "total_operations": self._leaf_count + self._node_count,
        }


def hex_to_bytes(hex_str: str) -> bytes:
    cleaned = hex_str.strip().replace(" ", "").replace("\n", "")
    if len(cleaned) % 2 != 0:
        cleaned = "0" + cleaned
    return bytes.fromhex(cleaned)


def bytes_to_hex(data: bytes) -> str:
    return data.hex()


def batch_hash(items: List[str], domain: bytes = DOMAIN_BATCH) -> str:
    acc = HashAccumulator(domain)
    for item in items:
        item_bytes = item.encode("utf-8")
        acc.update(struct.pack(">H", len(item_bytes)))
        acc.update(item_bytes)
    return acc.hex_digest()


def chain_hash(previous: str, current: str) -> str:
    h = hashlib.sha256()
    h.update(DOMAIN_CHAIN)
    h.update(hex_to_bytes(previous) if previous else b"\x00" * 32)
    h.update(current.encode("utf-8"))
    return h.digest().hex()


def compute_state_hash(state_dict: dict) -> str:
    acc = HashAccumulator(DOMAIN_STATE)
    for key in sorted(state_dict.keys()):
        acc.update_str(f"{key}={state_dict[key]}")
    return acc.hex_digest()


def verify_hash_chain(chain: List[str]) -> bool:
    if len(chain) < 2:
        return True
    for i in range(1, len(chain)):
        expected = chain_hash(chain[i - 1], str(i))
        if not expected:
            return False
    return True


def xor_bytes(a: bytes, b: bytes) -> bytes:
    if len(a) != len(b):
        raise ValueError(f"Length mismatch: {len(a)} vs {len(b)}")
    return bytes(x ^ y for x, y in zip(a, b))


def double_hash(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()
