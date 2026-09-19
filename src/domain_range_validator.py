import json
from pathlib import Path
from typing import Any

from rdflib import Graph, RDF, RDFS, URIRef

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ONTOLOGY_FILE = PROJECT_ROOT / "ontology" / "organization_ontology.ttl"
DATA_FILE = PROJECT_ROOT / "outputs" / "employees.ttl"
OUTPUT_FILE = PROJECT_ROOT / "outputs" / "collisions" / "domain_range_collisions.json"

def validate_domain_range() -> list[dict[str, Any]]:
    ontology = Graph()
    ontology.parse(ONTOLOGY_FILE, format="turtle")

    data = Graph()
    data.parse(DATA_FILE, format="turtle")

    property_rules: dict[Any, dict[str, Any]] = {}

    for prop, _, domain in ontology.triples((None, RDFS.domain, None)):
        property_rules.setdefault(prop, {})["domain"] = domain

    for prop, _, range_class in ontology.triples((None, RDFS.range, None)):
        property_rules.setdefault(prop, {})["range"] = range_class

    collisions: list[dict[str, Any]] = []

    for subject, predicate, obj in data:
        if predicate not in property_rules:
            continue

        rule = property_rules[predicate]

        expected_domain = rule.get("domain")
        expected_range = rule.get("range")

        if expected_domain is not None:
            subject_types = set(data.objects(subject, RDF.type))

            if expected_domain not in subject_types:
                collisions.append({
                    "type": "DOMAIN_VIOLATION",
                    "subject": str(subject),
                    "predicate": str(predicate),
                    "object": str(obj),
                    "expected_domain": str(expected_domain),
                    "actual_subject_types": [str(x) for x in subject_types],
                })

        if expected_range is not None and isinstance(obj, URIRef):
            object_types = set(data.objects(obj, RDF.type))

            if expected_range not in object_types:
                collisions.append({
                    "type": "RANGE_VIOLATION",
                    "subject": str(subject),
                    "predicate": str(predicate),
                    "object": str(obj),
                    "expected_range": str(expected_range),
                    "actual_object_types": [str(x) for x in object_types],
                })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_FILE.write_text(
        json.dumps(collisions, indent=2),
        encoding="utf-8"
    )

    print(f"Domain/range collisions found: {len(collisions):,}")
    print(f"Saved to: {OUTPUT_FILE}")

    return collisions

if __name__ == "__main__":
    validate_domain_range()
