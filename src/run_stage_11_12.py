from csv_to_rdf import build_graph
from collision_detector import run_collision_detector

def main():
    print("=" * 60)
    print("GSIS - STAGES 11 TO 12")
    print("=" * 60)

    print("\nStage 11: Build RDF graph")
    build_graph()

    print("\nStage 12: Semantic collision validation")
    run_collision_detector()

    print("\nStages 11-12 completed successfully.")

if __name__ == "__main__":
    main()