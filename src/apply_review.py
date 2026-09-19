from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REVIEW_FILE = PROJECT_ROOT / "outputs" / "review" / "human_review_queue.csv"
OUTPUT_FILE = PROJECT_ROOT / "outputs" / "review" / "reviewed_mappings.csv"

def apply_reviews():
    if not REVIEW_FILE.exists():
        raise FileNotFoundError(f"Review file not found: {REVIEW_FILE}")

    df = pd.read_csv(REVIEW_FILE)

    completed = df[
        df["review_status"].astype(str).str.upper() == "COMPLETED"
    ].copy()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    completed.to_csv(OUTPUT_FILE, index=False)

    print(f"Completed reviews exported: {len(completed):,}")
    print(f"Saved to: {OUTPUT_FILE}")
    return completed

if __name__ == "__main__":
    apply_reviews()
