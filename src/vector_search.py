from pathlib import Path
import pickle
from typing import Any

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONCEPT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "extracted_concepts.csv"
)

EMBEDDING_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "department_ontology_embeddings.pkl"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "department_vector_candidates.csv"
)

TOP_K = 3

def cosine_top_k(
    query_vector: np.ndarray,
    corpus_vectors: np.ndarray,
    k: int
):
    scores = corpus_vectors @ query_vector

    top_indices = np.argsort(scores)[::-1][:k]

    return [
        (int(index), float(scores[index]))
        for index in top_indices
    ]

def run_vector_search():
    if not CONCEPT_FILE.exists():
        raise FileNotFoundError(
            f"Missing extracted concept file: {CONCEPT_FILE}\n"
            "Run Stages 1-5 first."
        )

    if not EMBEDDING_FILE.exists():
        raise FileNotFoundError(
            f"Missing ontology embeddings: {EMBEDDING_FILE}\n"
            "Run generate_embeddings.py first."
        )

    concepts_df = pd.read_csv(CONCEPT_FILE)

    concepts_df = concepts_df[
        concepts_df["is_missing"] == False
    ].copy()

    with open(EMBEDDING_FILE, "rb") as f:
        payload = pickle.load(f)

    ontology = payload["ontology"]
    ontology_embeddings = payload["embeddings"]
    model_name = payload["model_name"]

    model: SentenceTransformer = SentenceTransformer(str(model_name))

    query_texts = (
        concepts_df["normalized_value"]
        .fillna("")
        .tolist()
    )

    query_embeddings = model.encode(
        query_texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    result_rows: list[dict[str, Any]] = []

    for row_index, (_, source_row) in enumerate(
        concepts_df.reset_index(drop=True).iterrows()
    ):

        source_value = source_row["source_value"]
        normalized_value = source_row["normalized_value"]
        record_count = int(source_row["record_count"])

        top_matches = cosine_top_k(
            query_embeddings[row_index],
            ontology_embeddings,
            TOP_K,
        )

        for rank, (ontology_index, score) in enumerate(
            top_matches,
            start=1
        ):
            candidate = ontology[ontology_index]

            result_rows.append({
                "source_value": source_value,
                "normalized_value": normalized_value,
                "record_count": record_count,
                "candidate_rank": rank,
                "candidate_concept_id": candidate["concept_id"],
                "candidate_label": candidate["canonical_label"],
                "similarity_score": round(score, 6),
            })

    result_df = pd.DataFrame(result_rows)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    result_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"Generated {len(result_df):,} candidate rows "
        f"for {concepts_df['source_value'].nunique():,} source concepts"
    )

    print(f"Saved to: {OUTPUT_FILE}")

    return result_df

if __name__ == "__main__":
    results = run_vector_search()

    print(
        results.head(30).to_string(index=False)
    )
