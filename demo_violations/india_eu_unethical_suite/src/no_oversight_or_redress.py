
from dataclasses import asdict

from .settings import POLICY


def system_governance_snapshot() -> dict:
    return {
        "human_oversight_enabled": not POLICY.skip_human_oversight,
        "user_notice_enabled": False,
        "right_to_explanation_enabled": not POLICY.skip_explanations,
        "appeals_channel_enabled": False,
        "grievance_officer_assigned": False,
        "retention_days": POLICY.retention_days,
        "consent_refresh_enabled": False,
        "audit_log_enabled": False,
        "policy": asdict(POLICY),
    }


if __name__ == "__main__":
    print(system_governance_snapshot())
