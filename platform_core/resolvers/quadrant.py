from django.utils import timezone


AM_DOMAINS = {
    1: "bos",
    2: "bridge",
    3: "openfields",
    4: "seedlings",
    5: "roots",
    6: "growth",
    7: "sunrise",
    8: "pathways",
    9: "community",
    10: "exchange",
    11: "harvestprep",
    12: "harvestcrops",
}

PM_DOMAINS = {
    1: "bos-domain",
    2: "bridge-domain",
    3: "openfields-domain",
    4: "seedlings-domain",
    5: "roots-domain",
    6: "growth-domain",
    7: "sunrise-domain",
    8: "pathways-domain",
    9: "community-domain",
    10: "exchange-domain",
    11: "harvestprep-domain",
    12: "harvestcrops-domain",
}


def get_current_hour():
    """
    Returns the current hour in 12-hour format (1-12) using server-local time.
    """
    now = timezone.localtime()
    hour = now.hour % 12
    return hour if hour != 0 else 12


def is_pm():
    """
    Returns True when the current server-local time is PM.
    """
    now = timezone.localtime()
    return now.hour >= 12


def resolve_domain(hour=None, pm=None):
    """
    Pure resolver for a quadrant hour.

    If `hour` is omitted, the current server-local hour is used.
    If `pm` is omitted, the current server-local AM/PM state is used.
    """
    normalized_hour = get_current_hour() if hour is None else int(hour)
    normalized_hour = ((normalized_hour - 1) % 12) + 1
    is_pm_value = is_pm() if pm is None else bool(pm)
    domain_map = PM_DOMAINS if is_pm_value else AM_DOMAINS
    return domain_map[normalized_hour]


def resolve_url(hour=None, pm=None):
    """
    Returns the canonical Django route for the resolved quadrant slug.

    AM routes through /center/grid/<slug>/ and PM routes through /domain/grid/<slug>/.
    """
    slug = resolve_domain(hour=hour, pm=pm)
    route_prefix = "domain" if (is_pm() if pm is None else bool(pm)) else "center"
    return f"/{route_prefix}/grid/{slug}/"
