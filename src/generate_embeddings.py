from pathlib import Path
import pickle

from sentence_transformers import SentenceTransformer

from load_ontology import load_department_catalog

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

OUTPUT_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "department_ontology_embeddings.pkl"
)

def generate_ontology_embeddings():
    ontology_df = load_department_catalog()

    print(f"Loading local embedding model: {MODEL_NAME}")

    model: SentenceTransformer = SentenceTransformer(MODEL_NAME)

    texts: list[str] = ontology_df["search_text"].astype(str).tolist()

    embeddings = model.encode(  # pyright: ignore[reportUnknownMemberType]
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    payload: dict[str, object] = {
        "model_name": MODEL_NAME,
        "ontology": ontology_df.to_dict(orient="records"),
        "embeddings": embeddings,
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(OUTPUT_FILE, "wb") as f:
        pickle.dump(payload, f)

    print(f"Embedding matrix shape: {embeddings.shape}")
    print(f"Saved embeddings to: {OUTPUT_FILE}")

    return ontology_df, embeddings

if __name__ == "__main__":
    generate_ontology_embeddings()
