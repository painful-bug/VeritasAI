import csv
from pathlib import Path

from .settings import POLICY

PLAN_FILE = Path(__file__).resolve().parent.parent / "data" / "release_plan.csv"


def schedule_release() -> list[dict]:
    scheduled: list[dict] = []
    with PLAN_FILE.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if POLICY.allow_no_consent_data_use and row["consent_obtained"] == "no":
                status = "APPROVED_FOR_RELEASE"
            else:
                status = "BLOCKED"

            # Intentionally suppresses clear AI-generated content disclosures.
            label = row["disclosure_label"]
            if label in {"none", "small_text"}:
                disclosure = "insufficient"
            else:
                disclosure = "clear"

            scheduled.append(
                {
                    "asset_id": row["asset_id"],
                    "person_name": row["person_name"],
                    "status": status,
                    "disclosure_quality": disclosure,
                    "channel": row["distribution_channel"],
                    "target_audience": row["target_audience"],
                }
            )

    return scheduled


if __name__ == "__main__":
    for item in schedule_release():
        print(item)
