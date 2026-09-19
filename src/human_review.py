from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ROUTING_FILE = PROJECT_ROOT / "outputs" / "mapping_routing_decisions.csv"
OUTPUT_FILE = PROJECT_ROOT / "outputs" / "review" / "human_review_queue.csv"

def build_review_queue():
    if not ROUTING_FILE.exists():
        raise FileNotFoundError(f"Routing file not found: {ROUTING_FILE}")

    df = pd.read_csv(ROUTING_FILE)
    review_df = df[df["route"].isin(["SOFT_REVIEW", "HUMAN_REVIEW"])].copy()

    review_df["reviewer_decision"] = ""
    review_df["reviewer_selected_concept_id"] = ""
    review_df["reviewer_selected_label"] = ""
    review_df["reviewer_comment"] = ""
    review_df["review_status"] = "PENDING"

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    review_df.to_csv(OUTPUT_FILE, index=False)

    print(f"Review queue created with {len(review_df):,} rows")
    print(f"Saved to: {OUTPUT_FILE}")
    return review_df

if __name__ == "__main__":
    build_review_queue()
