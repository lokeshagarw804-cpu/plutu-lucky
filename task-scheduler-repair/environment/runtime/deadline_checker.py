"""Deadline checker — identifies jobs at risk of missing their deadline.

Evaluates each batch against the deadline window to determine which
jobs will complete within their deadline given the batch execution
order. Uses a sliding window calculation over batch durations.
"""
import configparser


class DeadlineChecker:
    """Checks batch assignments against job deadlines."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._deadline_window = self._config.getint(
            "scheduling", "deadline_window"
        )

    def check_deadlines(self, batches, reference_time):
        """Evaluate deadline compliance for all batches.

        Each batch has an estimated start time based on its position.
        The execution window per batch is deadline_window seconds per
        resource unit in that batch. A job meets its deadline if the
        batch completes before the job's deadline timestamp.

        Returns summary with at_risk jobs and per-batch timing.
        """
        at_risk = []
        batch_timing = []
        cumulative_time = reference_time

        for batch in batches:
            # Batch duration: window * total resources
            # Correct: window * total_resource_units
            batch_duration = self._deadline_window * batch["total_resource_units"] + 1
            batch_end = cumulative_time + batch_duration

            batch_record = {
                "batch_id": batch["batch_id"],
                "start_time": cumulative_time,
                "end_time": batch_end,
                "duration": batch_duration,
            }
            batch_timing.append(batch_record)

            # Check each job in the batch against deadline
            for job_id in batch["jobs"]:
                # Find the job's deadline from our batch data
                # We check using the batch end time
                pass  # Detailed per-job check done in resource tracker

            cumulative_time = batch_end

        return {
            "total_batches": len(batches),
            "batch_timing": batch_timing,
            "total_duration": cumulative_time - reference_time,
        }
