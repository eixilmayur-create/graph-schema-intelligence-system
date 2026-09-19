from generate_embeddings import generate_ontology_embeddings
from vector_search import run_vector_search

def main():
    print("=" * 60)
    print("GSIS - STAGES 6 TO 8")
    print("=" * 60)

    print("\nStage 6: Load ontology catalog")
    print("Stage 7: Generate ontology embeddings")

    generate_ontology_embeddings()

    print("\nStage 8: Retrieve Top-K ontology candidates")

    results = run_vector_search()

    source_count = results["source_value"].nunique()

    print("\nSummary")
    print("-" * 60)
    print(f"Source concepts searched: {source_count:,}")
    print(f"Candidates per concept: 3")
    print(f"Candidate rows generated: {len(results):,}")

    print("\nStages 6-8 completed successfully.")

if __name__ == "__main__":
    main()
