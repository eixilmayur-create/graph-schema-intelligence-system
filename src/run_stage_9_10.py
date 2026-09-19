import argparse

from gemini_mapper import run_mapper
from confidence_router import run_router


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["mock", "gemini"], default="mock")
    parser.add_argument("--model", default="gemini-3.8-flash")
    args = parser.parse_args()

    print("=" * 60)
    print("GSIS - STAGES 9 TO 10")
    print("=" * 60)

    print("\nStage 9: Semantic mapping")
    run_mapper(mode=args.mode, model_name=args.model)

    print("\nStage 10: Confidence routing")
    df = run_router()

    print("\nSummary")
    print("-" * 60)
    print(f"Source concepts processed: {len(df):,}")

    for route, count in df["route"].value_counts().items():
        print(f"{route}: {count}")

    print("\nStages 9-10 completed successfully.")


if __name__ == "__main__":
    main()
