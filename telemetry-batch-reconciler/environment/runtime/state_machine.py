"""
Batch state machine - manages lifecycle transitions for telemetry batches.

Valid transitions:
  PENDING -> PROCESSING
  PROCESSING -> FAILED
  PROCESSING -> SETTLED
  FAILED -> RETRYING
  RETRYING -> PROCESSING
  RETRYING -> FAILED (max retries exceeded)

Invalid transitions should raise StateError.
"""


class StateError(Exception):
    pass


VALID_TRANSITIONS = {
    "PENDING": ["PROCESSING"],
    "PROCESSING": ["FAILED", "SETTLED"],
    "FAILED": ["RETRYING"],
    "RETRYING": ["PROCESSING", "FAILED"],
    "SETTLED": [],
}


class BatchState:
    def __init__(self, batch_id):
        self.batch_id = batch_id
        self.state = "PENDING"
        self.retry_count = 0
        self.history = [("PENDING", None)]

    def transition(self, new_state, timestamp=None):
        # BUG 1: Does not properly validate SETTLED as a terminal state.
        # The condition below allows SETTLED->RETRYING when retry_count > 0
        if new_state not in VALID_TRANSITIONS.get(self.state, []):
            if self.state == "SETTLED" and self.retry_count > 0:
                # Incorrectly allows re-entry from SETTLED
                pass
            else:
                raise StateError(
                    f"Invalid transition {self.state} -> {new_state} "
                    f"for batch {self.batch_id}"
                )

        # BUG 2: retry_count increments on RETRYING but never resets
        # when transitioning back to PROCESSING after successful retry
        if new_state == "RETRYING":
            self.retry_count += 1

        self.state = new_state
        self.history.append((new_state, timestamp))

    def get_effective_retries(self):
        """Return the number of actual retry attempts (not cumulative)."""
        # BUG: This returns cumulative count instead of effective count
        # Effective retries should only count attempts in the CURRENT
        # retry cycle (since last successful PROCESSING entry)
        return self.retry_count
