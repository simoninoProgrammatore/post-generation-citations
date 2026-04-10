"""
Step 3: Match atomic claims to supporting evidence passages.

Given a list of claims and a pool of candidate passages (provided 
by ALCE), this module determines which passages support each claim.

The primary method uses NLI (Natural Language Inference) to check 
if a passage entails a claim.
"""

import json
import argparse
from pathlib import Path


def match_with_nli(
    claim: str, 
    passages: list[dict], 
    model_name: str = "cross-encoder/nli-deberta-v3-large",
    threshold: float = 0.5,
    top_k: int = 3,
) -> list[dict]:
    """
    Find passages that support a claim using NLI.
    
    Args:
        claim: The atomic claim to verify.
        passages: List of candidate passages (each with 'text' and 'id').
        model_name: NLI cross-encoder model.
        threshold: Minimum entailment score to consider as support.
        top_k: Maximum number of supporting passages to return.
    
    Returns:
        List of matching passages with their entailment scores.
    """
    # TODO: Implement NLI-based matching
    # 1. Load cross-encoder model
    # 2. For each passage, compute entailment score: P(passage entails claim)
    # 3. Filter by threshold and return top-k
    raise NotImplementedError("Implement NLI-based claim-evidence matching.")


def match_with_similarity(
    claim: str, 
    passages: list[dict], 
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    top_k: int = 3,
) -> list[dict]:
    """
    Baseline: match claims to passages using embedding similarity.
    """
    # TODO: Implement embedding-based similarity matching
    raise NotImplementedError("Implement similarity-based matching.")


def run(input_path: str, output_path: str, method: str = "nli"):
    """
    Match all claims to supporting evidence.
    
    Args:
        input_path: Path to claims JSON (from Step 2).
        output_path: Path to save matched results.
        method: Matching method ('nli' or 'similarity').
    """
    with open(input_path, "r") as f:
        data = json.load(f)

    match_fn = {
        "nli": match_with_nli,
        "similarity": match_with_similarity,
    }[method]

    for example in data:
        passages = example.get("passages", [])
        matched_claims = []

        for claim in example["claims"]:
            matches = match_fn(claim, passages)
            matched_claims.append({
                "claim": claim,
                "supporting_passages": matches,
            })

        example["matched_claims"] = matched_claims

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    supported = sum(
        1 for ex in data 
        for mc in ex["matched_claims"] 
        if mc["supporting_passages"]
    )
    total = sum(len(ex["matched_claims"]) for ex in data)
    print(f"Matched {supported}/{total} claims with evidence -> {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Match claims to evidence")
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, default="results/matched.json")
    parser.add_argument("--method", type=str, default="nli", choices=["nli", "similarity"])
    args = parser.parse_args()
    run(args.input, args.output, args.method)
