from platform_core.resolvers.quadrant import resolve_domain, resolve_url


HINGE_HOUR = 12


def _normalize_hour(hour: int) -> int:
    return ((int(hour) - 1) % 12) + 1


def resolve_inversion_target(hour: int, pm: bool) -> tuple[int, bool, bool]:
    """
    Compartment-12 hinge rule.

    - If hour is 12, invert cycle: target is hour 1 in opposite mode.
    - Otherwise no inversion: target stays on same hour and mode.
    """
    normalized_hour = _normalize_hour(hour)
    is_pm_value = bool(pm)
    if normalized_hour == HINGE_HOUR:
        return 1, not is_pm_value, True
    return normalized_hour, is_pm_value, False


def build_inversion_payload(hour: int, pm: bool) -> dict:
    source_hour = _normalize_hour(hour)
    source_pm = bool(pm)
    target_hour, target_pm, is_active = resolve_inversion_target(source_hour, source_pm)

    return {
        "is_active": is_active,
        "hinge_hour": HINGE_HOUR,
        "source": {
            "hour": source_hour,
            "mode": "pm" if source_pm else "am",
        },
        "target": {
            "hour": target_hour,
            "mode": "pm" if target_pm else "am",
            "slug": resolve_domain(hour=target_hour, pm=target_pm),
            "url": resolve_url(hour=target_hour, pm=target_pm),
        },
    }
