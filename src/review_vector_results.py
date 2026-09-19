from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CANDIDATE_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "department_vector_candidates.csv"
)

def review_results():
    if not CANDIDATE_FILE.exists():
        raise FileNotFoundError(
            f"Candidate file not found: {CANDIDATE_FILE}"
        )

    df = pd.read_csv(CANDIDATE_FILE)

    top1 = (
        df[df["candidate_rank"] == 1]
        .sort_values(
            by="similarity_score",
            ascending=True
        )
    )

    print("\nLOWEST-CONFIDENCE TOP-1 MATCHES")
    print("=" * 90)

    print(
        top1.head(20).to_string(index=False)
    )

    print("\nHIGHEST-CONFIDENCE TOP-1 MATCHES")
    print("=" * 90)

    print(
        top1.tail(20)
        .sort_values(
            by="similarity_score",
            ascending=False
        )
        .to_string(index=False)
    )

if __name__ == "__main__":
    review_results()
