"""Audit chain verifier — main entry point.

Orchestrates the full audit verification: load streams, compute hash
chains, verify integrity windows, score results, detect tampering, and
produce the integrity report.
"""
import json
import os

from runtime.loader import StreamLoader
from runtime.hasher import ChainHasher
from runtime.verifier import ChainVerifier
from runtime.integrity_scorer import IntegrityScorer
from runtime.tamper_detector import TamperDetector


def main():
    config_path = "/app/runtime/config.ini"

    # Load audit streams
    loader = StreamLoader(config_path)
    streams = loader.load_streams()

    # Compute hash chains
    hasher = ChainHasher(config_path)
    chain_results = {}
    for stream_id, stream_data in streams.items():
        chain_results[stream_id] = hasher.compute_chain(stream_data)

    # Verify integrity per stream
    verifier = ChainVerifier(config_path)
    all_windows = []
    for stream_id, results in chain_results.items():
        windows = verifier.verify_stream(results, stream_id)
        all_windows.extend(windows)

    # Compute integrity scores
    scorer = IntegrityScorer()
    scores = scorer.compute_scores(all_windows)

    # Detect tampered entries
    detector = TamperDetector()
    tampered = detector.detect_tampered(all_windows, streams)

    # Write outputs
    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    # Integrity report
    report = {
        "stream_count": len(streams),
        "streams_verified": sorted(streams.keys()),
        "total_entries": scores["total_entries"],
        "total_valid": scores["total_valid"],
        "total_tampered": len(tampered),
        "aggregate_score": scores["aggregate_score"],
        "per_stream_scores": scores["per_stream_scores"],
        "hmac_key_length": hasher.get_key_length(),
    }
    with open(os.path.join(output_dir, "integrity_report.json"), "w") as f:
        json.dump(report, f, indent=2)

    # Tamper report
    tamper_report = {
        "tampered_count": len(tampered),
        "tampered_entries": tampered,
        "verification_windows": all_windows,
        "window_count": len(all_windows),
    }
    with open(os.path.join(output_dir, "tamper_report.json"), "w") as f:
        json.dump(tamper_report, f, indent=2)


if __name__ == "__main__":
    main()
