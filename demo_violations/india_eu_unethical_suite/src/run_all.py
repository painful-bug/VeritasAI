"""Runs all synthetic non-compliant fixtures and prints their outputs."""

from .biometric_surveillance import run_mass_surveillance
from .deepfake_campaign import schedule_release
from .hiring_bias_engine import auto_hire_or_reject
from .no_oversight_or_redress import system_governance_snapshot
from .social_scoring_system import assign_entitlements


def main() -> None:
    print("=== Hiring Bias Engine ===")
    for row in auto_hire_or_reject():
        print(row)

    print("\n=== Biometric Surveillance ===")
    for row in run_mass_surveillance():
        print(row)

    print("\n=== Social Scoring System ===")
    for row in assign_entitlements():
        print(row)

    print("\n=== Deepfake Campaign ===")
    for row in schedule_release():
        print(row)

    print("\n=== Governance Snapshot ===")
    print(system_governance_snapshot())


if __name__ == "__main__":
    main()
