import json
from pathlib import Path
from typing import Any

from domain_range_validator import validate_domain_range
from shacl_validator import run_shacl_validation

PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "collisions"
    / "collision_report.json"
)

def run_collision_detector() -> dict[str, Any]:
    domain_range = validate_domain_range()

    conforms, _, report_text = run_shacl_validation()

    result: dict[str, Any] = {
        "domain_range_collision_count": len(domain_range),
        "shacl_conforms": bool(conforms),
        "has_semantic_collision": (
            len(domain_range) > 0
            or not conforms
        ),
        "domain_range_collisions": domain_range[:100],
        "shacl_report_excerpt": report_text[:5000],
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_FILE.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8"
    )

    print("\nSEMANTIC COLLISION SUMMARY")
    print("=" * 60)
    print(
        f"Domain/range collisions: "
        f"{result['domain_range_collision_count']}"
    )
    print(
        f"SHACL conforms: "
        f"{result['shacl_conforms']}"
    )
    print(
        f"Semantic collision detected: "
        f"{result['has_semantic_collision']}"
    )

    print(f"\nSaved combined report to: {OUTPUT_FILE}")

    return result

if __name__ == "__main__":
    run_collision_detector()
