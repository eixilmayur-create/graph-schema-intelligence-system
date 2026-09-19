from pathlib import Path
import json
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_FILE = PROJECT_ROOT / "data" / "raw" / "employee_10k.csv"
ROUTING_FILE = PROJECT_ROOT / "outputs" / "mapping_routing_decisions.csv"
OUTPUT_FILE = PROJECT_ROOT / "outputs" / "metrics" / "evaluation_summary.json"

def evaluate_mapping():
    raw = pd.read_csv(RAW_FILE)
    routing = pd.read_csv(ROUTING_FILE)

    truth = (
        raw[["department_raw", "department_id_expected"]]
        .dropna()
        .drop_duplicates()
        .rename(columns={
            "department_raw": "source_value",
            "department_id_expected": "expected_concept_id"
        })
    )

    merged = routing.merge(truth, on="source_value", how="left")

    comparable = merged[
        merged["expected_concept_id"].notna()
        & merged["selected_concept_id"].notna()
    ].copy()

    overall_accuracy = None
    if not comparable.empty:
        overall_accuracy = float(
            (
                comparable["selected_concept_id"].astype(str)
                == comparable["expected_concept_id"].astype(str)
            ).mean()
        )

    auto = merged[
        (merged["route"] == "AUTO_APPROVE")
        & merged["expected_concept_id"].notna()
        & merged["selected_concept_id"].notna()
    ].copy()

    auto_accuracy = None
    if not auto.empty:
        auto_accuracy = float(
            (
                auto["selected_concept_id"].astype(str)
                == auto["expected_concept_id"].astype(str)
            ).mean()
        )

    summary = {
        "source_concepts": int(merged["source_value"].nunique()),
        "overall_mapping_accuracy": overall_accuracy,
        "auto_approved_concepts": int((merged["route"] == "AUTO_APPROVE").sum()),
        "soft_review_concepts": int((merged["route"] == "SOFT_REVIEW").sum()),
        "human_review_concepts": int((merged["route"] == "HUMAN_REVIEW").sum()),
        "auto_approval_accuracy": auto_accuracy,
        "evaluation_note": "Ground-truth columns are synthetic development labels."
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"Saved metrics to: {OUTPUT_FILE}")
    return summary

if __name__ == "__main__":
    evaluate_mapping()
