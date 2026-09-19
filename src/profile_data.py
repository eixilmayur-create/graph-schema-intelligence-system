import json
from pathlib import Path

from ingest import load_employee_data

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PROJECT_ROOT / "outputs" / "data_profile.json"

def profile_data():
    df = load_employee_data()

    profile = {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_values": {
            col: int(df[col].isna().sum())
            for col in df.columns
        },
        "unique_values": {
            "entity_type_raw": int(df["entity_type_raw"].nunique(dropna=True)),
            "department_raw": int(df["department_raw"].nunique(dropna=True)),
            "job_title_raw": int(df["job_title_raw"].nunique(dropna=True)),
            "relationship_type_raw": int(df["relationship_type_raw"].nunique(dropna=True)),
            "source_system": int(df["source_system"].nunique(dropna=True)),
        },
        "top_departments": (
            df["department_raw"]
            .fillna("<MISSING>")
            .value_counts()
            .head(20)
            .to_dict()
        ),
        "entity_type_distribution": (
            df["entity_type_raw"]
            .fillna("<MISSING>")
            .value_counts()
            .to_dict()
        ),
        "relationship_distribution": (
            df["relationship_type_raw"]
            .fillna("<MISSING>")
            .value_counts()
            .to_dict()
        ),
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(profile, indent=2),
        encoding="utf-8"
    )

    print(f"Profile saved to: {OUTPUT_FILE}")

    return profile

if __name__ == "__main__":
    profile = profile_data()
    print(json.dumps(profile, indent=2))
