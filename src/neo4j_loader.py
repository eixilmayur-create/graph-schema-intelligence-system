import json
import os
from pathlib import Path
from typing import Any, Callable, Iterator, LiteralString, TypeVar, TypedDict, cast

import pandas as pd
from neo4j import Driver, GraphDatabase, ManagedTransaction, Session

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CSV_FILE = PROJECT_ROOT / "data" / "raw" / "employee_10k.csv"
ROUTING_FILE = PROJECT_ROOT / "outputs" / "mapping_routing_decisions.csv"

BATCH_SIZE = 500
ItemT = TypeVar("ItemT")


class EmployeeRow(TypedDict):
    employee_id: str
    full_name: str | None
    email: str | None
    manager_id: str | None
    department_id: str | None
    department_label: str | None


def _setting(settings: dict[str, object], key: str, default: str | None = None) -> str | None:
    value = settings.get(key, default)
    return value if isinstance(value, str) else default


def get_connection_settings() -> tuple[str, str, str, str | None]:
    # Local defaults let the script run in a fresh VS Code terminal.
    # Environment variables can override them for another Neo4j instance.
    config_path = PROJECT_ROOT / "config" / "neo4j.json"
    raw_settings: Any = (
        json.loads(config_path.read_text(encoding="utf-8"))
        if config_path.exists()
        else {}
    )
    settings = cast(dict[str, object], raw_settings) if isinstance(raw_settings, dict) else {}
    uri = os.getenv("NEO4J_URI") or _setting(settings, "NEO4J_URI", "neo4j://localhost:7687")
    user = (os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER")
            or _setting(settings, "NEO4J_USERNAME", "neo4j"))
    password = os.getenv("NEO4J_PASSWORD") or _setting(settings, "NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE") or _setting(settings, "NEO4J_DATABASE")

    if not uri or not user or not password:
        raise EnvironmentError(
            "Set NEO4J_PASSWORD or add your connection settings to config/neo4j.json."
        )

    return uri, user, password, database


def load_mapping_lookup():
    if not ROUTING_FILE.exists():
        raise FileNotFoundError(
            f"Missing routing file: {ROUTING_FILE}"
        )

    routing = pd.read_csv(ROUTING_FILE)

    approved = routing[
        (routing["semantic_decision"] == "reuse")
        & (routing["route"] == "AUTO_APPROVE")
    ].copy()

    return {
        str(row["source_value"]): {
            "concept_id": str(row["selected_concept_id"]),
            "label": str(row["selected_label"]),
        }
        for _, row in approved.iterrows()
        if pd.notna(row["selected_concept_id"])
    }


def prepare_rows() -> list[EmployeeRow]:
    if not CSV_FILE.exists():
        raise FileNotFoundError(
            f"Missing employee file: {CSV_FILE}"
        )

    df = pd.read_csv(CSV_FILE)
    mapping_lookup = load_mapping_lookup()

    rows: list[EmployeeRow] = []

    for _, row in df.iterrows():
        department_raw = row.get("department_raw")

        mapping = (
            mapping_lookup.get(str(department_raw))
            if pd.notna(department_raw)
            else None
        )

        rows.append({
            "employee_id": str(row["employee_id"]),
            "full_name": None if pd.isna(row.get("full_name")) else str(row.get("full_name")),
            "email": None if pd.isna(row.get("email")) else str(row.get("email")),
            "manager_id": None if pd.isna(row.get("manager_id")) else str(row.get("manager_id")),
            "department_id": mapping["concept_id"] if mapping else None,
            "department_label": mapping["label"] if mapping else None,
        })

    return rows


def chunks(items: list[ItemT], size: int) -> Iterator[list[ItemT]]:
    for i in range(0, len(items), size):
        yield items[i:i + size]


def create_constraints(driver: Driver, database: str | None = None) -> None:
    queries = [
        """
        CREATE CONSTRAINT employee_id_unique
        IF NOT EXISTS
        FOR (e:Employee)
        REQUIRE e.employee_id IS UNIQUE
        """,
        """
        CREATE CONSTRAINT department_concept_unique
        IF NOT EXISTS
        FOR (d:Department)
        REQUIRE d.concept_id IS UNIQUE
        """,
    ]

    session_factory = cast(Callable[..., Session], getattr(driver, "session"))
    session = session_factory(database=database)
    with session:
        for query in queries:
            session.run(cast(LiteralString, query)).consume()


def load_batch(tx: ManagedTransaction, batch: list[EmployeeRow]) -> None:
    query = """
    UNWIND $rows AS row

    MERGE (e:Employee {employee_id: row.employee_id})
    SET e.full_name = row.full_name,
        e.email = row.email

    FOREACH (_ IN CASE
        WHEN row.department_id IS NOT NULL
        THEN [1] ELSE []
    END |
        MERGE (d:Department {concept_id: row.department_id})
        SET d.label = row.department_label
        MERGE (e)-[:WORKS_IN]->(d)
    )

    FOREACH (_ IN CASE
        WHEN row.manager_id IS NOT NULL
        AND row.manager_id <> ""
        AND row.manager_id <> row.employee_id
        THEN [1] ELSE []
    END |
        MERGE (m:Employee {employee_id: row.manager_id})
        MERGE (e)-[:REPORTS_TO]->(m)
    )
    """

    tx.run(cast(LiteralString, query), rows=batch).consume()


def load_to_neo4j():
    uri, user, password, database = get_connection_settings()

    driver_factory = cast(Callable[..., Driver], getattr(GraphDatabase, "driver"))
    driver = driver_factory(
        uri,
        auth=(user, password)
    )

    try:
        # Check authentication and the configured database before loading.
        session_factory = cast(Callable[..., Session], getattr(driver, "session"))
        session = session_factory(database=database)
        with session:
            session.run("RETURN 1 AS ok").consume()

        print("Connected to Neo4j.")

        create_constraints(driver, database)

        rows = prepare_rows()

        session_factory = cast(Callable[..., Session], getattr(driver, "session"))
        session = session_factory(database=database)
        with session:
            total = 0

            for batch in chunks(rows, BATCH_SIZE):
                session.execute_write(
                    load_batch,
                    batch
                )

                total += len(batch)

                print(
                    f"Loaded {total:,} / "
                    f"{len(rows):,} employee rows"
                )

        print("Neo4j load completed successfully.")

    finally:
        driver.close()


if __name__ == "__main__":
    load_to_neo4j()
