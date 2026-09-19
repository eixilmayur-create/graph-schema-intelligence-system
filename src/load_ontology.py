import json
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CATALOG_FILE = PROJECT_ROOT / "ontology" / "department_catalog.json"

def load_department_catalog() -> pd.DataFrame:
    if not CATALOG_FILE.exists():
        raise FileNotFoundError(
            f"Ontology catalog not found: {CATALOG_FILE}\n"
            "Place department_catalog.json inside ontology/"
        )

    with open(CATALOG_FILE, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    departments = catalog.get("departments", [])

    rows: list[dict[str, object]] = []

    for item in departments:
        concept_id = item["concept_id"]
        canonical_label = item["canonical_label"]
        aliases = item.get("aliases", [])

        rows.append({
            "concept_id": concept_id,
            "canonical_label": canonical_label,
            "search_text": " | ".join(
                [canonical_label] + aliases
            ),
            "entity_type": item.get("entity_type", "Department"),
            "status": item.get("status", "active"),
        })

    df = pd.DataFrame(rows)

    if df.empty:
        raise ValueError("No department concepts found in ontology catalog.")

    print(f"Loaded {len(df):,} ontology department concepts")

    return df

if __name__ == "__main__":
    ontology = load_department_catalog()
    print(ontology.to_string(index=False))
