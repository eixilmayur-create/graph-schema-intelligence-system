from pathlib import Path

import pandas as pd
from rdflib import Graph, Literal, Namespace, RDF

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CSV_FILE = PROJECT_ROOT / "data" / "raw" / "employee_10k.csv"
ROUTING_FILE = PROJECT_ROOT / "outputs" / "mapping_routing_decisions.csv"
OUTPUT_FILE = PROJECT_ROOT / "outputs" / "employees.ttl"

EX = Namespace("http://example.org/gsis/")

def safe_uri_fragment(value: str) -> str:
    return (
        str(value)
        .strip()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )

def load_mapping_lookup():
    if not ROUTING_FILE.exists():
        raise FileNotFoundError(
            f"Missing routing file: {ROUTING_FILE}\n"
            "Run Stages 9-10 first."
        )

    routing = pd.read_csv(ROUTING_FILE)

    approved = routing[
        routing["semantic_decision"] == "reuse"
    ].copy()

    return {
        str(row["source_value"]): str(row["selected_concept_id"])
        for _, row in approved.iterrows()
        if pd.notna(row["selected_concept_id"])
    }

def build_graph():
    if not CSV_FILE.exists():
        raise FileNotFoundError(
            f"Missing CSV file: {CSV_FILE}"
        )

    df = pd.read_csv(CSV_FILE)

    mapping_lookup = load_mapping_lookup()

    graph = Graph()
    graph.bind("ex", EX)

    for _, row in df.iterrows():
        employee_id = str(row["employee_id"])
        employee_uri = EX[f"employee/{safe_uri_fragment(employee_id)}"]

        graph.add((employee_uri, RDF.type, EX.Employee))
        graph.add((employee_uri, EX.employeeId, Literal(employee_id)))

        full_name = str(row.get("full_name", "")).strip()
        if full_name and full_name.lower() != "nan":
            graph.add((employee_uri, EX.fullName, Literal(full_name)))

        email = str(row.get("email", "")).strip()
        if email and email.lower() != "nan":
            graph.add((employee_uri, EX.email, Literal(email)))

        department_raw = row.get("department_raw")
        if pd.notna(department_raw):
            concept_id = mapping_lookup.get(str(department_raw))

            if concept_id:
                department_uri = EX[f"department/{safe_uri_fragment(concept_id)}"]
                graph.add((department_uri, RDF.type, EX.Department))
                graph.add((employee_uri, EX.worksIn, department_uri))

        manager_id = row.get("manager_id")
        relationship_type = str(
            row.get("relationship_type_raw", "")
        ).strip()

        if pd.notna(manager_id):
            manager_id = str(manager_id).strip()

            if manager_id:
                manager_uri = EX[f"employee/{safe_uri_fragment(manager_id)}"]

                if relationship_type == "reportsTo":
                    graph.add((employee_uri, EX.reportsTo, manager_uri))

                elif relationship_type == "locatedIn":
                    graph.add((employee_uri, EX.locatedIn, manager_uri))

                elif relationship_type == "managesLocation":
                    graph.add((employee_uri, EX.hasRole, manager_uri))

                elif relationship_type == "ownsDepartment":
                    graph.add((employee_uri, EX.worksIn, manager_uri))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(
        destination=str(OUTPUT_FILE),
        format="turtle"
    )

    print(f"RDF triples generated: {len(graph):,}")
    print(f"Saved RDF to: {OUTPUT_FILE}")

    return graph

if __name__ == "__main__":
    build_graph()
