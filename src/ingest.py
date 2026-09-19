from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "raw" / "employee_10k.csv"

REQUIRED_COLUMNS = {
    "employee_id",
    "full_name",
    "entity_type_raw",
    "department_raw",
    "job_title_raw",
    "manager_id",
    "relationship_type_raw",
    "source_system",
}

def load_employee_data() -> pd.DataFrame:
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {DATA_FILE}\n"
            "Place employee_10k.csv inside data/raw/"
        )

    df = pd.read_csv(DATA_FILE)

    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    print(f"Loaded {len(df):,} rows")
    print(f"Columns: {len(df.columns)}")

    return df

if __name__ == "__main__":
    data = load_employee_data()
    print(data.head())
