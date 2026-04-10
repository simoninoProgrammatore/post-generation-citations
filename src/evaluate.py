"""
Step 5: Evaluate cited responses using ALCE metrics.

Implements the evaluation dimensions from the ALCE framework 
(Gao et al., 2023):
  - Citation Precision (NLI): Are cited passages supporting the claims?
  - Citation Recall (NLI): Are all claims properly cited?
  - Correctness: Is the answer factually correct?
  - Fluency: Is the text natural and coherent?
"""

import json
import argparse
from pathlib import Path


def citation_precision_nli(
    response: str, 
    citations: list[dict], 
    nli_model_name: str = "cross-encoder/nli-deberta-v3-large",
) -> float:
    """
    Compute citation precision using NLI.
    
    For each citation in the response, check if the cited passage 
    actually entails the claim it is attached to.
    
    Returns:
        Precision score in [0, 1].
    """
    # TODO: Implement following ALCE methodology
    raise NotImplementedError("Implement Citation Precision NLI.")


def citation_recall_nli(
    response: str, 
    citations: list[dict],
    nli_model_name: str = "cross-encoder/nli-deberta-v3-large",
) -> float:
    """
    Compute citation recall using NLI.
    
    For each statement in the response, check if there exists 
    at least one citation whose passage entails the statement.
    
    Returns:
        Recall score in [0, 1].
    """
    # TODO: Implement following ALCE methodology
    raise NotImplementedError("Implement Citation Recall NLI.")


def correctness_exact_match(prediction: str, gold_answer: str) -> float:
    """
    Compute correctness via exact match (for ASQA short answers).
    """
    # TODO: Implement exact match scoring
    raise NotImplementedError("Implement Exact Match correctness.")


def correctness_claim_recall(
    prediction: str, 
    gold_claims: list[str],
    nli_model_name: str = "cross-encoder/nli-deberta-v3-large",
) -> float:
    """
    Compute claim recall: fraction of gold claims entailed by the response.
    """
    # TODO: Implement claim recall
    raise NotImplementedError("Implement Claim Recall.")


def fluency_mauve(predictions: list[str], references: list[str]) -> float:
    """
    Compute MAUVE score for fluency evaluation.
    """
    # TODO: Implement using mauve-text library
    raise NotImplementedError("Implement MAUVE fluency.")


def evaluate_all(input_path: str, output_path: str):
    """
    Run all evaluation metrics on cited responses.
    
    Args:
        input_path: Path to cited responses JSON (from Step 4).
        output_path: Path to save evaluation results.
    """
    with open(input_path, "r") as f:
        data = json.load(f)

    results = {
        "num_examples": len(data),
        "metrics": {},
        "per_example": [],
    }

    # TODO: Compute metrics for each example and aggregate
    # For each example:
    #   - citation_precision_nli
    #   - citation_recall_nli
    #   - correctness
    # Aggregate: mean across all examples
    # Also compute MAUVE on the full set

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Evaluation results saved -> {output_path}")
    for metric, value in results["metrics"].items():
        print(f"  {metric}: {value:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate cited responses")
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, default="results/evaluation.json")
    args = parser.parse_args()
    evaluate_all(args.input, args.output)
