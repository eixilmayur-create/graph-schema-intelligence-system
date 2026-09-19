import json
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DECISION_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "gemini_mapping_decisions.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "mapping_routing_decisions.csv"
)

AUTO_APPROVE_THRESHOLD = 0.90
SOFT_REVIEW_THRESHOLD = 0.70


def determine_route(decision: str, confidence: float, risk_flags: list[str]) -> str:
    severe_risks = {
        "LOW_VECTOR_SIMILARITY",
        "AMBIGUOUS_TOP_CANDIDATES",
        "POSSIBLE_NEW_CONCEPT",
    }

    has_severe_risk = bool(severe_risks.intersection(set(risk_flags)))

    if decision in {"create_new", "uncertain"}:
        return "HUMAN_REVIEW"

    if confidence >= AUTO_APPROVE_THRESHOLD and not has_severe_risk:
        return "AUTO_APPROVE"

    if confidence >= SOFT_REVIEW_THRESHOLD:
        return "SOFT_REVIEW"

    return "HUMAN_REVIEW"


def run_router():
    if not DECISION_FILE.exists():
        raise FileNotFoundError(
            f"Mapping decision file not found: {DECISION_FILE}\n"
            "Run gemini_mapper.py first."
        )

    decisions = json.loads(DECISION_FILE.read_text(encoding="utf-8"))

    routed_rows = []

    for item in decisions:
        risk_flags = item.get("risk_flags", [])

        route = determine_route(
            decision=item["decision"],
            confidence=float(item["confidence"]),
            risk_flags=risk_flags,
        )

        routed_rows.append({
            "source_value": item["source_value"],
            "semantic_decision": item["decision"],
            "selected_concept_id": item.get("selected_concept_id"),
            "selected_label": item.get("selected_label"),
            "confidence": round(float(item["confidence"]), 6),
            "route": route,
            "risk_flags": "|".join(risk_flags),
            "reasoning": item["reasoning"],
        })

    df = pd.DataFrame(routed_rows)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print("\nROUTING SUMMARY")
    print("=" * 60)

    summary = df["route"].value_counts().to_dict()

    for route in ["AUTO_APPROVE", "SOFT_REVIEW", "HUMAN_REVIEW"]:
        print(f"{route:<20} {summary.get(route, 0):>5}")

    print(f"\nRouting decisions saved to: {OUTPUT_FILE}")
    return df


if __name__ == "__main__":
    result = run_router()
    print("\nExample routed mappings:\n")
    print(result.head(20).to_string(index=False))
