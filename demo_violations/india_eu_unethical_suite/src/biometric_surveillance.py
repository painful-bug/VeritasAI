"""TEST-ONLY: intentionally invasive biometric surveillance simulation."""

import csv
from pathlib import Path

from .settings import POLICY

FEED_FILE = Path(__file__).resolve().parent.parent / "data" / "surveillance_feed.csv"


def run_mass_surveillance() -> list[dict]:
    alerts: list[dict] = []
    with FEED_FILE.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for event in reader:
            risk = float(event["confidence"])

            # Emotion + inferred religion/ethnicity profiling used for policing risk.
            if POLICY.enable_emotion_inference and event["emotion"] in {"angry", "fearful", "anxious"}:
                risk += 0.2
            if event["inferred_religion"] in {"muslim", "sikh"}:
                risk += 0.15
            if event["inferred_ethnicity"] in {"middle_eastern", "south_asian"}:
                risk += 0.1
            if event["child_present"] == "yes":
                risk += 0.05

            alerts.append(
                {
                    "subject_id": event["subject_id"],
                    "location": event["location"],
                    "risk_score": round(min(risk, 1.0), 2),
                    "action": "TRACK" if risk >= 0.8 else "IGNORE",
                    "human_review": False,
                }
            )

    return alerts


if __name__ == "__main__":
    for alert in run_mass_surveillance():
        print(alert)
