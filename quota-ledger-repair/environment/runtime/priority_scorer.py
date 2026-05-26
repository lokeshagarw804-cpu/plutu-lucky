"""
Priority scorer module — assigns priority scores to requests based on
their organizational distance from the root team using exponential decay.
"""


# Organizational hierarchy for distance calculation
TEAM_HIERARCHY = {
    "platform-core": 0,
    "platform-services": 1,
    "platform-external": 2,
}


def compute_priority_score(priority_group, config):
    """
    Compute priority score for a given priority group.

    Score = base_priority * (decay_factor ** distance)
    Where distance is the organizational distance from root_team.

    Root team (distance 0) should receive the full base_priority.
    """
    base_priority = config.getfloat("scoring", "base_priority")
    decay_factor = config.getfloat("scoring", "decay_factor")

    distance = TEAM_HIERARCHY.get(priority_group, len(TEAM_HIERARCHY))

    score = base_priority * (decay_factor ** (distance + 1))
    return round(score, 2)


def assign_priority_scores(requests, config):
    """
    Assign priority scores to all requests based on their priority_group.
    Returns requests annotated with 'priority_score' field.
    """
    scored = []
    for req in requests:
        result = dict(req)
        pg = req.get("priority_group", "unknown")
        result["priority_score"] = compute_priority_score(pg, config)
        scored.append(result)

    return scored
