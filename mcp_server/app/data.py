from datetime import UTC, datetime, timedelta


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def days_from_now_iso(days: int) -> str:
    return (datetime.now(UTC) + timedelta(days=days)).isoformat(
        timespec="seconds"
    )


# Mock company directory. "active" mirrors an HR/IdP feed; deactivated
# accounts should fail access checks and resets gracefully rather than
# silently succeeding.
DIRECTORY = {
    "alice@quantumintegrators.com": {
        "display_name": "Alice Chen",
        "manager_email": "priya@quantumintegrators.com",
        "active": True,
    },
    "bob@quantumintegrators.com": {
        "display_name": "Bob Diaz",
        "manager_email": "priya@quantumintegrators.com",
        "active": True,
    },
    "priya@quantumintegrators.com": {
        "display_name": "Priya Rao",
        "manager_email": None,
        "active": True,
    },
    "old.contractor@quantumintegrators.com": {
        "display_name": "Former Contractor",
        "manager_email": "priya@quantumintegrators.com",
        "active": False,
    },
}

KNOWN_RESOURCES = {"shared_drive", "vpn", "finance_erp", "engineering_repo"}

# (user_email, resource) -> has_access. Absence defaults to False (not
# provisioned) for any known resource/user pair not listed here.
RESOURCE_ACCESS = {
    ("alice@quantumintegrators.com", "shared_drive"): True,
    ("alice@quantumintegrators.com", "vpn"): True,
    ("alice@quantumintegrators.com", "engineering_repo"): True,
    ("bob@quantumintegrators.com", "shared_drive"): False,
    ("bob@quantumintegrators.com", "vpn"): True,
    ("priya@quantumintegrators.com", "finance_erp"): True,
}

ASSETS = {
    "LAP-1001": {
        "owner_email": "alice@quantumintegrators.com",
        "status": "active",
        "battery_health_pct": 91,
    },
    "LAP-1002": {
        "owner_email": "bob@quantumintegrators.com",
        "status": "in_repair",
        "battery_health_pct": 54,
    },
    "LAP-1003": {
        "owner_email": "old.contractor@quantumintegrators.com",
        "status": "retired",
        "battery_health_pct": None,
    },
}

# auto_approve software skips manager review; everything else routes to
# pending_manager_review unless the requester provides no justification, in
# which case it's denied outright.
SOFTWARE_CATALOG = {
    "figma": {"auto_approve": True, "cost_tier": "low"},
    "slack_premium": {"auto_approve": True, "cost_tier": "low"},
    "adobe_creative_cloud": {"auto_approve": False, "cost_tier": "high"},
    "jetbrains_all_products": {"auto_approve": False, "cost_tier": "medium"},
}
