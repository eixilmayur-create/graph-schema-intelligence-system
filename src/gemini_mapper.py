import argparse
import json
import os
from pathlib import Path
from typing import Literal

import pandas as pd
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CANDIDATES_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "department_vector_candidates.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "gemini_mapping_decisions.json"
)

DEFAULT_MODEL = "gemini-3.8-flash"


class MappingDecision(BaseModel):
    source_value: str
    decision: Literal["reuse", "create_new", "uncertain"]
    selected_concept_id: str | None = None
    selected_label: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    risk_flags: list[str] = []


def load_candidate_groups():
    if not CANDIDATES_FILE.exists():
        raise FileNotFoundError(
            f"Candidate file not found: {CANDIDATES_FILE}\n"
            "Run Stages 6-8 first."
        )

    df = pd.read_csv(CANDIDATES_FILE)
    groups = []

    for source_value, group in df.groupby("source_value", sort=False):
        group = group.sort_values("candidate_rank")
        candidates = []

        for _, row in group.iterrows():
            candidates.append({
                "rank": int(row["candidate_rank"]),
                "concept_id": row["candidate_concept_id"],
                "label": row["candidate_label"],
                "similarity": float(row["similarity_score"]),
            })

        groups.append({
            "source_value": source_value,
            "normalized_value": group.iloc[0]["normalized_value"],
            "record_count": int(group.iloc[0]["record_count"]),
            "candidates": candidates,
        })

    return groups


def mock_decision(item: dict) -> MappingDecision:
    candidates = item["candidates"]

    top1 = candidates[0]
    top2 = candidates[1] if len(candidates) > 1 else None

    top1_score = top1["similarity"]
    margin = top1_score - top2["similarity"] if top2 else top1_score

    source_norm = str(item["normalized_value"]).strip().lower()
    label_norm = str(top1["label"]).strip().lower()

    exact_match = source_norm == label_norm

    risk_flags = []

    if top1_score < 0.55:
        risk_flags.append("LOW_VECTOR_SIMILARITY")

    if margin < 0.08:
        risk_flags.append("AMBIGUOUS_TOP_CANDIDATES")

    if exact_match:
        return MappingDecision(
            source_value=item["source_value"],
            decision="reuse",
            selected_concept_id=top1["concept_id"],
            selected_label=top1["label"],
            confidence=0.99,
            reasoning="The normalized source label exactly matches the canonical ontology label.",
            risk_flags=risk_flags,
        )

    if top1_score >= 0.80 and margin >= 0.12:
        confidence = min(
            0.99,
            0.72 + (0.20 * top1_score) + (0.20 * min(margin, 0.35))
        )

        return MappingDecision(
            source_value=item["source_value"],
            decision="reuse",
            selected_concept_id=top1["concept_id"],
            selected_label=top1["label"],
            confidence=confidence,
            reasoning=(
                "The top ontology candidate has strong semantic similarity "
                "and is clearly separated from the second-ranked candidate."
            ),
            risk_flags=risk_flags,
        )

    if top1_score >= 0.58 and margin >= 0.06:
        confidence = min(
            0.88,
            0.52 + (0.22 * top1_score) + (0.35 * min(margin, 0.30))
        )

        return MappingDecision(
            source_value=item["source_value"],
            decision="reuse",
            selected_concept_id=top1["concept_id"],
            selected_label=top1["label"],
            confidence=confidence,
            reasoning=(
                "The top candidate is plausible, but the mapping is not strong enough "
                "for high-confidence automation."
            ),
            risk_flags=risk_flags,
        )

    if top1_score < 0.45 and margin < 0.10:
        return MappingDecision(
            source_value=item["source_value"],
            decision="create_new",
            selected_concept_id=None,
            selected_label=None,
            confidence=0.72,
            reasoning=(
                "No existing ontology candidate is sufficiently similar to justify semantic reuse."
            ),
            risk_flags=risk_flags + ["POSSIBLE_NEW_CONCEPT"],
        )

    return MappingDecision(
        source_value=item["source_value"],
        decision="uncertain",
        selected_concept_id=top1["concept_id"],
        selected_label=top1["label"],
        confidence=0.58,
        reasoning=(
            "The candidates are not sufficiently distinct to make a reliable autonomous mapping decision."
        ),
        risk_flags=risk_flags,
    )


def build_prompt(item: dict) -> str:
    candidate_text = "\n".join(
        [
            f"- rank={c['rank']}, concept_id={c['concept_id']}, "
            f"label={c['label']}, vector_similarity={c['similarity']:.4f}"
            for c in item["candidates"]
        ]
    )

    return f"""
You are the semantic mapping layer of an enterprise Graph Schema Intelligence System.

Decide whether the incoming department should:
- reuse an existing ontology concept
- be treated as a possible new concept
- remain uncertain

Incoming source value:
{item["source_value"]}

Normalized value:
{item["normalized_value"]}

Number of records using this value:
{item["record_count"]}

Retrieved ontology candidates:
{candidate_text}

Rules:
1. Prefer reuse only when semantic equivalence is clear.
2. Vector similarity is evidence, not final truth.
3. Consider ambiguity between top candidates.
4. Be conservative when confidence is low.
5. Confidence reflects semantic certainty, not just vector score.
6. For create_new, selected_concept_id and selected_label must be null.
7. Add concise risk flags where appropriate.
""".strip()


def gemini_decision(item: dict, model_name: str) -> MappingDecision:
    from google import genai

    client = genai.Client()

    interaction = client.interactions.create(
        model=model_name,
        input=build_prompt(item),
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": MappingDecision.model_json_schema(),
        },
    )

    decision = MappingDecision.model_validate_json(interaction.output_text)

    if decision.decision == "reuse" and not decision.selected_concept_id:
        raise ValueError("Gemini returned reuse without selected_concept_id.")

    if decision.decision == "create_new":
        decision.selected_concept_id = None
        decision.selected_label = None

    return decision


def run_mapper(mode: str = "mock", model_name: str = DEFAULT_MODEL):
    groups = load_candidate_groups()
    results = []

    print(
        f"Running semantic mapper in {mode.upper()} mode "
        f"for {len(groups):,} source concepts"
    )

    if mode == "gemini" and not os.getenv("GEMINI_API_KEY"):
        raise EnvironmentError(
            "GEMINI_API_KEY is not set.\n"
            'PowerShell example: $env:GEMINI_API_KEY="YOUR_KEY"'
        )

    for index, item in enumerate(groups, start=1):
        if mode == "mock":
            decision = mock_decision(item)
        else:
            decision = gemini_decision(item, model_name)

        results.append(decision.model_dump())

        print(
            f"[{index}/{len(groups)}] {item['source_value']} "
            f"-> {decision.decision} ({decision.confidence:.3f})"
        )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )

    print(f"\nMapping decisions saved to: {OUTPUT_FILE}")
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["mock", "gemini"], default="mock")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    run_mapper(mode=args.mode, model_name=args.model)


if __name__ == "__main__":
    main()
