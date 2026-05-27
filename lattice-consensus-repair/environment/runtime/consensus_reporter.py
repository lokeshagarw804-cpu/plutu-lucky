"""Consensus reporter — generates summary statistics and reports.

Produces aggregate metrics about DAG health, finality progress, and
per-validator contribution statistics. The report includes both a
detailed per-transaction finality map and high-level consensus metrics.
"""


class ConsensusReporter:
    """Generates consensus analysis reports from finality data."""

    def generate_report(self, all_txs, finality, validators, tx_weights):
        """Build comprehensive consensus report.

        Returns two structures:
        1. finality_map: per-transaction finality details ordered by
           causal timestamp (timestamp, validator_id, seq)
        2. consensus_summary: aggregate metrics
        """
        # Build ordered finality map
        finality_map = []
        for tx in all_txs:
            tx_id = tx["tx_id"]
            info = finality[tx_id]
            finality_map.append({
                "tx_id": tx_id,
                "validator_id": info["validator_id"],
                "round": info["round"],
                "timestamp": tx["timestamp"],
                "is_final": info["is_final"],
                "normalized_weight": info["normalized_weight"],
                "depth_reached": info["depth_reached"],
            })

        # Compute per-validator statistics
        validator_stats = {}
        for vid in sorted(validators.keys()):
            vtxs = [tx for tx in all_txs if tx["validator_id"] == vid]
            final_count = sum(
                1 for tx in vtxs if finality[tx["tx_id"]]["is_final"]
            )
            validator_stats[vid] = {
                "validator_id": vid,
                "total_transactions": len(vtxs),
                "finalized_count": final_count,
                "stake": validators[vid]["stake"],
                "finality_rate": round(final_count / len(vtxs), 4) if vtxs else 0.0,
            }

        total_txs = len(all_txs)
        total_final = sum(1 for f in finality.values() if f["is_final"])

        summary = {
            "total_transactions": total_txs,
            "total_finalized": total_final,
            "finality_rate": round(total_final / total_txs, 4) if total_txs > 0 else 0.0,
            "total_validators": len(validators),
            "validator_stats": validator_stats,
            "rounds_processed": max(tx["round"] for tx in all_txs),
        }

        return finality_map, summary
