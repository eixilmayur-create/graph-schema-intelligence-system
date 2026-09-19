from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ROUTING_FILE = PROJECT_ROOT / "outputs" / "mapping_routing_decisions.csv"
REVIEW_FILE = PROJECT_ROOT / "outputs" / "review" / "human_review_queue.csv"
OUTPUT_FILE = PROJECT_ROOT / "outputs" / "review" / "mapping_feedback_store.csv"

def build_feedback_store():
    routing = pd.read_csv(ROUTING_FILE)
    review = pd.read_csv(REVIEW_FILE) if REVIEW_FILE.exists() else pd.DataFrame()

    rows = []

    for _, row in routing.iterrows():
        source_value = str(row["source_value"])
        match = review[review["source_value"].astype(str) == source_value] if not review.empty else pd.DataFrame()

        final_decision = row["semantic_decision"]
        final_concept_id = row["selected_concept_id"]
        final_label = row["selected_label"]
        feedback_source = "MODEL"
        review_status = "NOT_REQUIRED"

        if not match.empty:
            r = match.iloc[0]
            review_status = str(r.get("review_status", "PENDING"))

            if review_status.upper() == "COMPLETED":
                final_decision = r.get("reviewer_decision")
                final_concept_id = r.get("reviewer_selected_concept_id")
                final_label = r.get("reviewer_selected_label")
                feedback_source = "HUMAN"

        rows.append({
            "source_value": source_value,
            "model_decision": row["semantic_decision"],
            "model_selected_concept_id": row["selected_concept_id"],
            "model_selected_label": row["selected_label"],
            "model_confidence": row["confidence"],
            "route": row["route"],
            "review_status": review_status,
            "final_decision": final_decision,
            "final_concept_id": final_concept_id,
            "final_label": final_label,
            "feedback_source": feedback_source,
        })

    feedback = pd.DataFrame(rows)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    feedback.to_csv(OUTPUT_FILE, index=False)

    print(f"Feedback records written: {len(feedback):,}")
    print(f"Saved to: {OUTPUT_FILE}")
    return feedback

if __name__ == "__main__":
    build_feedback_store()
