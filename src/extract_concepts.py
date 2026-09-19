from pathlib import Path

from ingest import load_employee_data
from normalize_concepts import normalize_label

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "extracted_concepts.csv"
)

def extract_concepts():
    df = load_employee_data()

    department_counts = (
        df["department_raw"]
        .fillna("")
        .value_counts(dropna=False)
        .reset_index()
    )

    department_counts.columns = [
        "source_value",
        "record_count"
    ]

    department_counts["concept_type"] = "Department"

    department_counts["normalized_value"] = (
        department_counts["source_value"]
        .apply(normalize_label)
    )

    department_counts["is_missing"] = (
        department_counts["normalized_value"] == ""
    )

    department_counts = department_counts[
        [
            "concept_type",
            "source_value",
            "normalized_value",
            "record_count",
            "is_missing",
        ]
    ].sort_values(
        by=["is_missing", "record_count"],
        ascending=[True, False]
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    department_counts.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"Extracted "
        f"{len(department_counts):,} "
        f"unique department concepts"
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )

    return department_counts

if __name__ == "__main__":
    concepts = extract_concepts()
    print(concepts.head(20).to_string(index=False))
