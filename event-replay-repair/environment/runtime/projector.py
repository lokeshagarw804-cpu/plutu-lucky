"""Event projector — builds materialized account state from events.

Processes a sequenced event stream and maintains running account
balances. Each event modifies the balance for its target account
based on event type and amount.
"""
import configparser


class EventProjector:
    """Projects domain events into materialized account balances."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._initial = self._config.getfloat("projection", "initial_balance")
        self._decimals = self._config.getint("projection", "decimal_places")

    def project(self, sequenced_events):
        """Apply events in sequence to build account state.

        Returns dict mapping account_id to final balance.
        Each event has: account_id, event_type, amount, timestamp.
        Event types: credit (adds), debit (subtracts).
        """
        balances = {}

        for event in sequenced_events:
            acct = event["account_id"]
            if acct not in balances:
                balances[acct] = self._initial

            amount = round(event["amount"], self._decimals)
            if event["event_type"] == "credit":
                balances[acct] = round(balances[acct] + amount, self._decimals)
            elif event["event_type"] == "debit":
                balances[acct] = round(balances[acct] - amount, self._decimals)

        return balances
