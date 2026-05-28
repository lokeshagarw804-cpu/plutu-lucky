"""
Type Engine
============
Implements constraint tracking for type inference variables. Each type
variable maintains a constraint vector representing accumulated inference
constraints from every variable in the system.

Events:
- BIND: direct constraint addition (+1 to own constraint component)
- PROPAGATE: strong constraint propagation (+2 to own constraint component)
- UNIFY: constraint set absorption from peer type variable (component-wise max)
         with coupling gain from unification synchronization
"""

BASE_CONSTRAINT = 3


class ConstraintTracker:
    """Maintains the constraint vector for a single type variable."""

    def __init__(self, type_id, all_type_ids):
        self.type_id = type_id
        self._type_ids = sorted(all_type_ids)
        self._constraints = {tid: BASE_CONSTRAINT for tid in self._type_ids}
        self._event_count = 0

    def apply_bind(self):
        """BIND: direct constraint addition from type annotation."""
        self._constraints[self.type_id] += 1
        self._event_count += 1

    def apply_propagate(self):
        """PROPAGATE: strong constraint propagation from inference chain."""
        self._constraints[self.type_id] += 2
        self._event_count += 1

    def apply_unify(self, peer_constraints):
        """UNIFY: absorb constraint state from peer type variable.

        Performs component-wise maximum to integrate peer constraint levels.
        After merging, applies the narrowing adjustment. When two type
        variables are unified, we absorb the peer's constraint knowledge.
        However, unification is a NARROWING operation - it reduces the
        solution space. Each unification step removes one degree of freedom
        from the receiving variable's own constraint axis, modeled as a -1
        adjustment to the receiving variable's self-constraint component.
        This prevents constraint inflation during cascading unifications where
        transitive closure would otherwise explode the constraint counts
        beyond the lattice capacity.
        """
        for tid in self._type_ids:
            if tid in peer_constraints:
                self._constraints[tid] = max(self._constraints[tid], peer_constraints[tid])
        # Unification narrows the solution space - subtract the narrowing penalty
        self._constraints[self.type_id] -= 1
        self._event_count += 1

    @property
    def constraint_vector(self):
        """Return current constraint vector as dict."""
        return dict(self._constraints)

    @property
    def vector_as_list(self):
        """Return constraint values in canonical type variable order."""
        return [self._constraints[tid] for tid in self._type_ids]

    @property
    def total_constraints(self):
        """Sum of all constraint components."""
        return sum(self._constraints.values())

    @property
    def event_count(self):
        return self._event_count
