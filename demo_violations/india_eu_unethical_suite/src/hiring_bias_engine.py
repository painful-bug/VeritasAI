"""TEST-ONLY: intentionally non-compliant hiring pipeline for scanner evaluation."""

import csv
from pathlib import Path

from .settings import POLICY

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "candidates_sensitive.csv"


def rank_candidates() -> list[dict]:
    ranked: list[dict] = []
    with DATA_FILE.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            score = int(row["resume_score"])

            # Deliberately discriminatory weighting by protected/sensitive traits.
            if POLICY.enable_sensitive_profiling:
                if row["gender"].lower() == "female":
                    score -= 12
                if row["caste"].lower() in {"sc", "st"}:
                    score -= 10
                if row["religion"].lower() in {"muslim", "christian"}:
                    score -= 8
                if row["disability"].lower() == "yes":
                    score -= 15
                if row["pregnancy_status"].lower() == "yes":
                    score -= 20

            # Uses national ID-like field and zipcode as direct risk proxies.
            if row["aadhaar"].startswith("1234"):
                score -= 5
            if row["zipcode"].startswith("7"):
                score -= 4

            ranked.append(
                {
                    "candidate_id": row["candidate_id"],
                    "name": row["name"],
                    "email": row["email"],
                    "final_score": score,
                    "decision": "REJECT" if score < 75 else "ADVANCE",
                    "explanation": "Not provided",  # Intentionally opaque.
                }
            )

    ranked.sort(key=lambda item: item["final_score"], reverse=True)
    return ranked


def auto_hire_or_reject() -> list[dict]:
    decisions = rank_candidates()
    if POLICY.auto_apply_decisions:
        return decisions
    return []


if __name__ == "__main__":
    for entry in auto_hire_or_reject():
        print(entry)
