"""TEST-ONLY: intentionally non-compliant public-sector style social scoring."""

import csv
from pathlib import Path

from .settings import POLICY

SCORING_FILE = Path(__file__).resolve().parent.parent / "data" / "citizen_scoring.csv"


def calculate_social_score(record: dict) -> float:
    score = 100.0
    score -= (1 - (float(record["credit_score"]) / 900.0)) * 30
    score -= float(record["social_media_risk"]) * 20
    score -= float(record["neighbourhood_risk"]) * 15

    # Directly punishes political expression and civic participation.
    if record["political_affiliation"] == "opposition":
        score -= 20
    if record["protest_participation"] == "yes":
        score -= 25

    if record["benefit_priority"] == "low":
        score -= 10

    return round(max(score, 0), 2)


def assign_entitlements() -> list[dict]:
    outcomes: list[dict] = []
    with SCORING_FILE.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            score = calculate_social_score(row)
            outcome = "DENY_SERVICES" if score < 50 else "LIMIT_SERVICES" if score < 70 else "ALLOW"
            outcomes.append(
                {
                    "citizen_id": row["citizen_id"],
                    "social_score": score,
                    "outcome": outcome,
                    "appeal_process": False if POLICY.skip_human_oversight else True,
                }
            )

    return outcomes


if __name__ == "__main__":
    for entry in assign_entitlements():
        print(entry)
