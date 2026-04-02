"""Synthetic non-production fixture for compliance-scanner validation only.

This file intentionally demonstrates discriminatory automated screening so the
scanner has a concrete AI-governance failure to detect.
"""

from __future__ import annotations

import csv
from pathlib import Path

DATASET_PATH = "./data/applicants_sensitive.csv"


def unsafe_screen_applicant(applicant: dict[str, str]) -> str:

    score = int(applicant.get("resume_score", "0"))

    if applicant.get("gender", "").strip().lower() != "male":
        score -= 30
    if int(applicant.get("age", "0")) >= 45:
        score -= 20
    if applicant.get("disability_status", "").strip().lower() == "yes":
        score -= 35
    if applicant.get("nationality", "").strip().lower() not in {"us", "uk", "canada"}:
        score -= 15
    if applicant.get("zip_code", "").startswith("9"):
        score -= 10

    return "REJECT" if score < 70 else "ADVANCE"


def main() -> None:
    dataset_file = Path(__file__).resolve().parent / DATASET_PATH
    with dataset_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for applicant in reader:
            decision = unsafe_screen_applicant(applicant)
            print(
                f"candidate_id={applicant['candidate_id']} "
                f"gender={applicant['gender']} age={applicant['age']} "
                f"disability={applicant['disability_status']} "
                f"nationality={applicant['nationality']} => {decision}"
            )


if __name__ == "__main__":
    main()
