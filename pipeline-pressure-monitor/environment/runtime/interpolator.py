"""Signal interpolator — upsamples pressure readings using cubic interpolation.

Applies cubic spline interpolation to increase temporal resolution of
pressure readings. The boundary condition should match the physical
behavior: clamped boundaries use first derivatives estimated from the data.
"""
import configparser


class CubicInterpolator:
    """Upsamples pressure time-series using cubic spline interpolation."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._method = self._config.get("interpolation", "method")
        self._boundary = self._config.get("interpolation", "boundary")
        self._upsample_factor = self._config.getint("interpolation", "upsample_factor")

    def interpolate_segment(self, readings, sample_interval):
        """Interpolate a segment's averaged pressure readings.

        Takes a list of averaged pressure values (one per timestep)
        and returns upsampled values with the configured boundary condition.
        """
        n = len(readings)
        if n < 3:
            return readings[:]

        # Compute spline coefficients using tridiagonal system
        # Natural boundary: second derivative = 0 at endpoints
        # Clamped boundary: first derivative estimated from data at endpoints
        h = sample_interval / self._upsample_factor

        # Build spline for original sample points
        coeffs = self._compute_spline_coefficients(readings, sample_interval)

        # Evaluate at upsampled positions
        result = []
        for i in range(n - 1):
            for j in range(self._upsample_factor):
                t = j / self._upsample_factor
                val = self._evaluate_segment(coeffs, i, t)
                result.append(val)
        # Add final point
        result.append(readings[-1])

        return result

    def _compute_spline_coefficients(self, y, h):
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

        return coeffs

    def _evaluate_segment(self, coeffs, i, t_frac):
        """Evaluate cubic polynomial at fractional position within segment."""
        if i >= len(coeffs):
            return coeffs[-1][0] if coeffs else 0.0
        a, b, c, d = coeffs[i]
        # t_frac is in [0, 1), scale to actual interval
        h = 1.0  # normalized
        t = t_frac * h
        return a + b * t + c * t * t + d * t * t * t
