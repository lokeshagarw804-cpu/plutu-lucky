#!/usr/bin/env python3
"""Repair script for pipeline pressure monitoring system."""
import os
import sys


def patch_gradient_calculator():
    """Fix gradient denominator: use delta_time instead of segment_length."""
    path = "/app/runtime/gradient_calculator.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug A: Replace segment_length denominator with delta_time
    # The gradient is dP/dt, so denominator should be time step, not length
    old_code = '''            # Forward difference for first point
            # BUG: divides by segment_length instead of delta_time
            # The denominator should be 2*delta_time for central and
            # delta_time for forward/backward
            seg_length = self._lengths[position]

            grad.append((pressures[1] - pressures[0]) / seg_length)

            # Central difference for interior points
            for i in range(1, n - 1):
                grad.append(
                    (pressures[i + 1] - pressures[i - 1]) / (2 * seg_length)
                )

            # Backward difference for last point
            grad.append((pressures[-1] - pressures[-2]) / seg_length)'''

    new_code = '''            # Forward difference for first point
            grad.append((pressures[1] - pressures[0]) / self._delta_time)

            # Central difference for interior points
            for i in range(1, n - 1):
                grad.append(
                    (pressures[i + 1] - pressures[i - 1]) / (2 * self._delta_time)
                )

            # Backward difference for last point
            grad.append((pressures[-1] - pressures[-2]) / self._delta_time)'''

    content = content.replace(old_code, new_code)

    with open(path, "w") as f:
        f.write(content)


def patch_aggregator():
    """Fix window slice off-by-one: use window_size instead of window_size-1."""
    path = "/app/runtime/aggregator.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug B: slice should include full window_size elements
    content = content.replace(
        "window_data = [grad_values[k] for k in range(pos, pos + self._window_size - 1)]",
        "window_data = [grad_values[k] for k in range(pos, pos + self._window_size)]"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_threshold_engine():
    """Fix bidirectional detection and event classification."""
    path = "/app/runtime/threshold_engine.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug C: use abs() for bidirectional threshold comparison
    content = content.replace(
        "if mean_grad > self._threshold:",
        "if abs(mean_grad) > self._threshold:"
    )

    # Fix Bug D: classify events by dominant gradient direction
    # Replace all "type": "surge" with conditional classification
    old_event_mid = '''                        events.append({
                            "segment_id": seg_id,
                            "start_window": run_start,
                            "end_window": run_start + run_length - 1,
                            "duration_windows": run_length,
                            "type": "surge",
                            "peak_magnitude": self._get_peak_in_run(
                                windows, run_start, run_length
                            ),
                        })
                    run_start = None
                    run_length = 0

            # Check final run
            if run_length >= self._min_duration:
                events.append({
                    "segment_id": seg_id,
                    "start_window": run_start,
                    "end_window": run_start + run_length - 1,
                    "duration_windows": run_length,
                    "type": "surge",
                    "peak_magnitude": self._get_peak_in_run(
                        windows, run_start, run_length
                    ),
                })'''

    new_event_mid = '''                        event_type = self._classify_run(windows, run_start, run_length)
                        events.append({
                            "segment_id": seg_id,
                            "start_window": run_start,
                            "end_window": run_start + run_length - 1,
                            "duration_windows": run_length,
                            "type": event_type,
                            "peak_magnitude": self._get_peak_in_run(
                                windows, run_start, run_length
                            ),
                        })
                    run_start = None
                    run_length = 0

            # Check final run
            if run_length >= self._min_duration:
                event_type = self._classify_run(windows, run_start, run_length)
                events.append({
                    "segment_id": seg_id,
                    "start_window": run_start,
                    "end_window": run_start + run_length - 1,
                    "duration_windows": run_length,
                    "type": event_type,
                    "peak_magnitude": self._get_peak_in_run(
                        windows, run_start, run_length
                    ),
                })'''

    content = content.replace(old_event_mid, new_event_mid)

    # Add the classification helper method before _get_peak_in_run
    classify_method = '''
    def _classify_run(self, windows, start, length):
        """Classify event run by dominant gradient direction."""
        total_grad = 0.0
        for i in range(start, start + length):
            if i < len(windows):
                total_grad += windows[i]["mean_gradient"]
        return "surge" if total_grad > 0 else "leak"

'''
    content = content.replace(
        "    def _get_peak_in_run(self, windows, start, length):",
        classify_method + "    def _get_peak_in_run(self, windows, start, length):"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_interpolator():
    """Fix boundary conditions: implement clamped instead of natural."""
    path = "/app/runtime/interpolator.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug E: replace natural boundary (M[0]=M[n-1]=0) with clamped
    # Clamped uses estimated end derivatives from data
    old_spline = '''    def _compute_spline_coefficients(self, y, h):
        """Compute cubic spline coefficients using tridiagonal solver.

        Uses natural boundary conditions (second derivative = 0 at endpoints).
        """
        n = len(y)
        # Tridiagonal system for second derivatives (moments)
        # M[0] = M[n-1] = 0 for natural spline
        m = [0.0] * n

        # BUG: Uses natural boundary (M[0]=M[n-1]=0) instead of clamped
        # Clamped should estimate end derivatives from data:
        #   M[0] derived from (y[1]-y[0])/h as the slope constraint
        #   M[n-1] derived from (y[n-1]-y[n-2])/h as the slope constraint

        # Interior points: solve tridiagonal system
        # For natural: standard tridiagonal with M[0]=M[n-1]=0
        if n < 3:
            return [(y[i], 0.0, 0.0, 0.0) for i in range(n)]

        # Build tridiagonal system for interior moments
        # Equation: h/6*M[i-1] + 2h/3*M[i] + h/6*M[i+1] = (y[i+1]-2y[i]+y[i-1])/h
        alpha = [0.0] * n
        beta = [0.0] * n

        # Forward sweep
        for i in range(1, n - 1):
            rhs = (y[i + 1] - 2 * y[i] + y[i - 1]) / h
            denom = 2.0 * h / 3.0
            if i > 1:
                denom -= (h / 6.0) * alpha[i - 1]
            alpha[i] = -(h / 6.0) / denom
            if i > 1:
                beta[i] = (rhs - (h / 6.0) * beta[i - 1]) / denom
            else:
                beta[i] = rhs / denom

        # Back substitution
        for i in range(n - 2, 0, -1):
            m[i] = alpha[i] * m[i + 1] + beta[i]

        # Build segment coefficients: (a, b, c, d) for each interval
        coeffs = []
        for i in range(n - 1):
            a = y[i]
            b = (y[i + 1] - y[i]) / h - h * (2 * m[i] + m[i + 1]) / 6.0
            c = m[i] / 2.0
            d = (m[i + 1] - m[i]) / (6.0 * h)
            coeffs.append((a, b, c, d))

        return coeffs'''

    new_spline = '''    def _compute_spline_coefficients(self, y, h):
        """Compute cubic spline coefficients using tridiagonal solver.

        Uses clamped boundary conditions (first derivative estimated from data).
        """
        n = len(y)
        m = [0.0] * n

        if n < 3:
            return [(y[i], 0.0, 0.0, 0.0) for i in range(n)]

        # Clamped boundary: estimate end derivatives from data
        d0 = (y[1] - y[0]) / h  # first derivative at start
        dn = (y[-1] - y[-2]) / h  # first derivative at end

        # Build tridiagonal system including boundary constraints
        # Clamped: 2h/3*M[0] + h/6*M[1] = (y[1]-y[0])/h - d0
        #          h/6*M[n-2] + 2h/3*M[n-1] = dn - (y[n-1]-y[n-2])/h
        alpha = [0.0] * n
        beta = [0.0] * n

        # Start boundary
        rhs_0 = (y[1] - y[0]) / h - d0
        denom_0 = 2.0 * h / 3.0
        alpha[0] = -(h / 6.0) / denom_0
        beta[0] = rhs_0 / denom_0

        # Interior points
        for i in range(1, n - 1):
            rhs = (y[i + 1] - 2 * y[i] + y[i - 1]) / h
            denom = 2.0 * h / 3.0 - (h / 6.0) * alpha[i - 1]
            alpha[i] = -(h / 6.0) / denom
            beta[i] = (rhs - (h / 6.0) * beta[i - 1]) / denom

        # End boundary
        rhs_n = dn - (y[-1] - y[-2]) / h
        denom_n = 2.0 * h / 3.0 - (h / 6.0) * alpha[n - 2]
        m[n - 1] = (rhs_n - (h / 6.0) * beta[n - 2]) / denom_n

        # Back substitution
        for i in range(n - 2, -1, -1):
            m[i] = alpha[i] * m[i + 1] + beta[i]

        # Build segment coefficients: (a, b, c, d) for each interval
        coeffs = []
        for i in range(n - 1):
            a = y[i]
            b = (y[i + 1] - y[i]) / h - h * (2 * m[i] + m[i + 1]) / 6.0
            c = m[i] / 2.0
            d = (m[i + 1] - m[i]) / (6.0 * h)
            coeffs.append((a, b, c, d))

        return coeffs'''

    content = content.replace(old_spline, new_spline)

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_gradient_calculator()
    patch_aggregator()
    patch_threshold_engine()
    patch_interpolator()

    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_pipeline import main as run_main
    run_main()


if __name__ == "__main__":
    main()
