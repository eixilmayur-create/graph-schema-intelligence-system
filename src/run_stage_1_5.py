from profile_data import profile_data
from extract_concepts import extract_concepts

def main():
    print("=" * 60)
    print("GSIS - STAGES 1 TO 5")
    print("=" * 60)

    print("\nStage 1-2: Ingestion and profiling")
    profile = profile_data()

    print("\nStage 3-5: Schema discovery, concept extraction and normalization")
    concepts = extract_concepts()

    print("\nSummary")
    print("-" * 60)
    print(f"Rows loaded: {profile['row_count']:,}")
    print(f"Columns discovered: {profile['column_count']}")
    print(f"Unique department concepts: {len(concepts):,}")
    print(f"Missing department concepts: {int(concepts['is_missing'].sum())}")

    print("\nStages 1-5 completed successfully.")

if __name__ == "__main__":
    main()
