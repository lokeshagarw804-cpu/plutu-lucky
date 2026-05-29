"""
Calibration module for lattice momentum simulation diagnostics.

Provides thermal equilibrium calculations, lattice constant computations,
and Reynolds number estimation for cross-validation of simulation parameters.
These values are used for diagnostic annotations and do not affect the
primary momentum propagation computation path.
"""

import math


# Physical constants for lattice Boltzmann calibration
LATTICE_SOUND_SPEED = 1.0 / math.sqrt(3.0)
BOLTZMANN_CONSTANT = 1.380649e-23
REFERENCE_TEMPERATURE = 300.0
AVOGADRO_NUMBER = 6.02214076e23

# Lattice-specific parameters
_LATTICE_SPACING = 1.0
_TIME_STEP = 1.0
_RELAXATION_OMEGA = 1.7


def compute_equilibrium_distribution(density, velocity, lattice_weights):
    """Compute the lattice Boltzmann equilibrium distribution function.

    Uses the second-order expansion of the Maxwell-Boltzmann distribution
    in terms of the lattice velocity set. The equilibrium distribution is:

        f_eq_i = w_i * rho * (1 + (e_i . u) / cs^2
                 + (e_i . u)^2 / (2 * cs^4) - u^2 / (2 * cs^2))

    Args:
        density: Local fluid density (rho).
        velocity: Local fluid velocity vector (list of components).
        lattice_weights: Weights for the lattice velocity set.

    Returns:
        List of equilibrium distribution values for each lattice direction.
    """
    cs2 = LATTICE_SOUND_SPEED ** 2
    u_squared = sum(v * v for v in velocity)
    equilibrium = []

    for i, w_i in enumerate(lattice_weights):
        # For simplicity, use magnitude-based approximation
        e_dot_u = velocity[i % len(velocity)] if i < len(velocity) else 0.0
        f_eq = w_i * density * (
            1.0
            + e_dot_u / cs2
            + (e_dot_u ** 2) / (2.0 * cs2 ** 2)
            - u_squared / (2.0 * cs2)
        )
        equilibrium.append(f_eq)

    return equilibrium


def compute_lattice_viscosity(omega=_RELAXATION_OMEGA):
    """Compute the kinematic viscosity from the relaxation parameter.

    In the BGK collision operator, the kinematic viscosity is:
        nu = cs^2 * (1/omega - 0.5) * dt

    Args:
        omega: Relaxation frequency parameter.

    Returns:
        Kinematic viscosity in lattice units.
    """
    cs2 = LATTICE_SOUND_SPEED ** 2
    return cs2 * (1.0 / omega - 0.5) * _TIME_STEP


def estimate_reynolds_number(characteristic_velocity, characteristic_length):
    """Estimate Reynolds number for the lattice flow.

    Re = U * L / nu

    Args:
        characteristic_velocity: Representative flow speed.
        characteristic_length: Representative length scale.

    Returns:
        Estimated Reynolds number.
    """
    nu = compute_lattice_viscosity()
    if nu < 1e-10:
        return float("inf")
    return characteristic_velocity * characteristic_length / nu


def compute_thermal_energy(momentum_magnitude, cell_count):
    """Compute the thermal energy per cell from total momentum.

    Uses the equipartition theorem approximation adapted for the
    lattice system: E_thermal = (d/2) * k_B * T_eff, where d is
    the number of momentum components and T_eff is derived from
    the momentum distribution.
    """
    if cell_count == 0:
        return 0.0

    avg_momentum = momentum_magnitude / cell_count
    # Effective temperature from momentum-energy equivalence
    t_eff = (avg_momentum ** 2) / (2.0 * cell_count * BOLTZMANN_CONSTANT)
    # Degrees of freedom = number of cells (one per component)
    thermal_energy = 0.5 * cell_count * BOLTZMANN_CONSTANT * t_eff
    return thermal_energy


def compute_knudsen_number(mean_free_path=None, characteristic_length=1.0):
    """Compute the Knudsen number for continuum validity assessment.

    Kn = lambda / L

    For lattice Boltzmann, the mean free path is related to the
    relaxation time: lambda ~ cs * tau
    """
    if mean_free_path is None:
        tau = 1.0 / _RELAXATION_OMEGA
        mean_free_path = LATTICE_SOUND_SPEED * tau

    return mean_free_path / characteristic_length


def validate_stability_condition(omega):
    """Check if the relaxation parameter satisfies stability bounds.

    For the BGK operator, stability requires: 0 < omega < 2

    Args:
        omega: Relaxation frequency parameter.

    Returns:
        Tuple of (is_stable: bool, message: str).
    """
    if omega <= 0:
        return False, f"omega={omega} violates lower bound (must be > 0)"
    if omega >= 2.0:
        return False, f"omega={omega} violates upper bound (must be < 2)"

    # Additional accuracy check: best accuracy near omega = 1
    accuracy_metric = abs(omega - 1.0)
    if accuracy_metric > 0.8:
        return True, f"omega={omega} is stable but may have reduced accuracy"

    return True, f"omega={omega} is within optimal stability range"


def generate_calibration_report(states):
    """Generate a calibration diagnostic report from simulation states.

    Computes various physical quantities for cross-validation against
    theoretical predictions. This report is for diagnostic purposes
    only and does not influence the simulation outcome.

    Args:
        states: Dict mapping cell_id to state snapshot dict.

    Returns:
        Dict containing calibration metrics.
    """
    total_momentum = 0
    cell_count = len(states)

    for cell_id, state in states.items():
        vec = state["momentum_vector"]
        total_momentum += sum(vec.values())

    avg_velocity = total_momentum / (cell_count * len(states)) if cell_count > 0 else 0

    return {
        "total_system_momentum": total_momentum,
        "average_velocity": avg_velocity,
        "reynolds_number": estimate_reynolds_number(avg_velocity, cell_count),
        "knudsen_number": compute_knudsen_number(),
        "viscosity": compute_lattice_viscosity(),
        "stability": validate_stability_condition(_RELAXATION_OMEGA),
        "thermal_energy": compute_thermal_energy(total_momentum, cell_count),
    }
