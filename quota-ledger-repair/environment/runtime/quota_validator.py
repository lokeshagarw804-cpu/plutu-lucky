"""
Quota validator module — checks each allocation request against the
configured quota policy limits and marks requests as approved or rejected.
"""

import configparser


REFERENCE_TIME = 1700000000


def validate_quotas(requests, config):
    """
    Validate each request against quota limits.
    Returns a list of validated request dicts with 'quota_status' field.

    Requests exceeding the maximum allocation units are marked as 'rejected'.
    Requests within limits are marked as 'approved'.
    """
    max_units = config.getint("limits", "max_allocation_units")
    max_burst = config.getfloat("limits", "max_burst_factor")
    allowed_tiers = config.get("limits", "allowed_tiers").split(",")

    validated = []
    for req in requests:
        result = dict(req)
        tier = req.get("tier", "")
        units = req.get("requested_units", 0)

        if tier not in allowed_tiers:
            result["quota_status"] = "rejected"
            result["rejection_reason"] = "invalid_tier"
        elif units > max_units:
            result["quota_status"] = "rejected"
            result["rejection_reason"] = "over_quota"
        else:
            result["quota_status"] = "approved"
            result["rejection_reason"] = None

        validated.append(result)

    return validated
