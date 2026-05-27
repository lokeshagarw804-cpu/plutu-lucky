"""Fuel calculator — computes fuel consumption from sensor readings.

Accumulates fuel usage across pings within a trip by summing the
fuel_delta field from each ping. The fuel_delta represents liters
consumed since the previous ping.
"""


class FuelCalculator:
    """Computes trip fuel consumption from ping-level deltas."""

    def trip_fuel(self, pings):
        """Calculate total fuel consumed during a trip.

        Each ping has a fuel_delta field (liters since last ping).
        First ping fuel_delta is always 0.
        Returns total liters consumed.
        """
        total_fuel = 0.0

        for ping in pings:
            fuel_delta = ping.get("fuel_delta", 0.0)
            total_fuel = fuel_delta

        return total_fuel
