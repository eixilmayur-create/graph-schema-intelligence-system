from human_review import build_review_queue
from feedback_loop import build_feedback_store
from evaluate_pipeline import evaluate_mapping

def main():
    print("=" * 60)
    print("GSIS - STAGES 13 TO 15")
    print("=" * 60)

    print("\nStage 13: Human review queue")
    build_review_queue()

    print("\nStage 15: Feedback store")
    build_feedback_store()

    print("\nStage 15: Evaluation metrics")
    evaluate_mapping()

    print("\nStage 14 (Neo4j) runs separately after credentials are configured:")
    print("python src/neo4j_loader.py")

if __name__ == "__main__":
    main()
