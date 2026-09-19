from pathlib import Path
import json
from typing import cast

from pyshacl import validate  # pyright: ignore[reportUnknownVariableType]
from rdflib import Graph


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = PROJECT_ROOT / "outputs" / "employees.ttl"
SHAPES_FILE = PROJECT_ROOT / "shapes" / "employee_shapes.ttl"
ONTOLOGY_FILE = PROJECT_ROOT / "ontology" / "organization_ontology.ttl"

REPORT_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "validation"
    / "shacl_report.ttl"
)

SUMMARY_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "validation"
    / "shacl_summary.json"
)


def run_shacl_validation() -> tuple[bool, Graph, str]:

    print("Loading RDF data...")

    data_graph = Graph()
    data_graph.parse(
        str(DATA_FILE),
        format="turtle"
    )

    print("Loading SHACL shapes...")

    shapes_graph = Graph()
    shapes_graph.parse(
        str(SHAPES_FILE),
        format="turtle"
    )

    print("Loading ontology...")

    ontology_graph = Graph()
    ontology_graph.parse(
        str(ONTOLOGY_FILE),
        format="turtle"
    )

    print("Running SHACL validation...")

    validation_result = cast(
        tuple[bool, Graph, str],
        validate(
            data_graph,
            shacl_graph=shapes_graph,
            ont_graph=ontology_graph,
            inference="rdfs",
            abort_on_first=False,
            allow_infos=True,
            allow_warnings=True,
            advanced=True,
        ),
    )
    conforms_result, report_graph_result, report_text_result = validation_result

    conforms = bool(conforms_result)
    report_graph = report_graph_result
    report_text = str(report_text_result)

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    report_graph.serialize(
        destination=str(REPORT_FILE),
        format="turtle"
    )

    summary: dict[str, bool | str] = {
        "conforms": bool(conforms),
        "report_text": str(report_text),
    }

    SUMMARY_FILE.write_text(
        json.dumps(
            summary,
            indent=2
        ),
        encoding="utf-8"
    )

    print()
    print(f"SHACL conforms: {conforms}")
    print(f"Report: {REPORT_FILE}")
    print(f"Summary: {SUMMARY_FILE}")

    return conforms, report_graph, report_text


if __name__ == "__main__":
    run_shacl_validation()