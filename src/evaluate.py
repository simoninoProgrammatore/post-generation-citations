"""
Step 5: Evaluate cited responses using ALCE metrics.

Implements the evaluation dimensions from the ALCE framework
(Gao et al., 2023):
  - Citation Precision (NLI): Are cited passages supporting the claims?
  - Citation Recall (NLI): Are all claims properly cited?
  - Correctness: Is the answer factually correct?
  - Fluency: Is the text natural and coherent?
"""

import re
import json
import argparse
import numpy as np
from pathlib import Path
from functools import lru_cache


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_nli_model(model_name: str = "cross-encoder/nli-deberta-v3-large"):
    """Load and cache the NLI cross-encoder model."""
    from sentence_transformers import CrossEncoder
    return CrossEncoder(model_name)


def _nli_entailment_score(premise: str, hypothesis: str, model_name: str) -> float:
    """
    Compute the entailment probability P(premise ⊨ hypothesis).
    """
    model = _load_nli_model(model_name)
    scores = model.predict([(premise, hypothesis)])
    logits = np.array(scores)
    if logits.ndim == 2:
        logits = logits[0]
    exp = np.exp(logits - np.max(logits))
    probs = exp / exp.sum()
    return float(probs[1])


def _has_cuda() -> bool:
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


# ──────────────────────────────────────────────
# Citation Precision (NLI) — claim-level
# ──────────────────────────────────────────────

def citation_precision_nli(
    matched_claims: list[dict],
    nli_model_name: str = "cross-encoder/nli-deberta-v3-large",
    threshold: float = 0.5,
) -> float:
    """
    Compute citation precision at claim level using NLI.

    For each (claim, cited passage) pair, check if the passage
    actually entails the claim.

    Precision = supported pairs / total pairs

    Args:
        matched_claims: List of claims with their supporting passages.
        nli_model_name: NLI model to use.
        threshold:      Entailment score threshold.

    Returns:
        Precision score in [0, 1].
    """
    # Build all (passage_text, claim) pairs for batch predict
    pairs = []
    for mc in matched_claims:
        claim = mc["claim"]
        for passage in mc["supporting_passages"]:
            pairs.append((passage.get("text", ""), claim))

    if not pairs:
        return 0.0

    model = _load_nli_model(nli_model_name)
    all_scores = model.predict(pairs)
    all_scores = np.array(all_scores)
    if all_scores.ndim == 1:
        all_scores = all_scores.reshape(1, -1)

    exp = np.exp(all_scores - np.max(all_scores, axis=1, keepdims=True))
    probs = exp / exp.sum(axis=1, keepdims=True)
    entailment_probs = probs[:, 1]

    supported = int(np.sum(entailment_probs >= threshold))
    return supported / len(pairs)


# ──────────────────────────────────────────────
# Citation Recall (NLI) — claim-level
# ──────────────────────────────────────────────

def citation_recall_nli(
    matched_claims: list[dict],
    nli_model_name: str = "cross-encoder/nli-deberta-v3-large",
    threshold: float = 0.5,
) -> float:
    """
    Compute citation recall at claim level using NLI.

    For each claim, check if at least one of its cited passages
    entails the claim.

    Recall = claims with at least one valid citation / total claims

    Args:
        matched_claims: List of claims with their supporting passages.
        nli_model_name: NLI model to use.
        threshold:      Entailment score threshold.

    Returns:
        Recall score in [0, 1].
    """
    if not matched_claims:
        return 0.0

    # Build all pairs, tracking which claim they belong to
    pairs = []
    claim_indices = []

    for claim_idx, mc in enumerate(matched_claims):
        claim = mc["claim"]
        for passage in mc["supporting_passages"]:
            pairs.append((passage.get("text", ""), claim))
            claim_indices.append(claim_idx)

    if not pairs:
        return 0.0

    model = _load_nli_model(nli_model_name)
    all_scores = model.predict(pairs)
    all_scores = np.array(all_scores)
    if all_scores.ndim == 1:
        all_scores = all_scores.reshape(1, -1)

    exp = np.exp(all_scores - np.max(all_scores, axis=1, keepdims=True))
    probs = exp / exp.sum(axis=1, keepdims=True)
    entailment_probs = probs[:, 1]

    # For each claim, check if at least one passage entails it
    supported_claims = set()
    for i, score in enumerate(entailment_probs):
        if score >= threshold:
            supported_claims.add(claim_indices[i])

    return len(supported_claims) / len(matched_claims)


# ──────────────────────────────────────────────
# Correctness: Exact Match
# ──────────────────────────────────────────────

def correctness_exact_match(prediction: str, gold_answers: list[str]) -> float:
    """
    Compute correctness via exact match (for ASQA short answers).
    Case-insensitive substring match.
    """
    if not gold_answers:
        return 0.0
    prediction_lower = prediction.lower()
    hits = sum(1 for ans in gold_answers if ans.lower() in prediction_lower)
    return hits / len(gold_answers)


# ──────────────────────────────────────────────
# Correctness: Claim Recall
# ──────────────────────────────────────────────

def correctness_claim_recall(
    prediction: str,
    gold_claims: list[str],
    nli_model_name: str = "cross-encoder/nli-deberta-v3-large",
    threshold: float = 0.5,
) -> float:
    """
    Compute claim recall: fraction of gold claims entailed by the response.
    """
    if not gold_claims:
        return 0.0

    entailed = 0
    for claim in gold_claims:
        score = _nli_entailment_score(
            premise=prediction,
            hypothesis=claim,
            model_name=nli_model_name,
        )
        if score >= threshold:
            entailed += 1

    return entailed / len(gold_claims)


# ──────────────────────────────────────────────
# Fluency: MAUVE
# ──────────────────────────────────────────────

def fluency_mauve(predictions: list[str], references: list[str]) -> float:
    """
    Compute MAUVE score for fluency evaluation.
    Computed at corpus level, not per-example.
    """
    import mauve

    if not predictions or not references:
        return 0.0

    result = mauve.compute_mauve(
        p_text=references,
        q_text=predictions,
        device_id=0 if _has_cuda() else -1,
        max_text_length=512,
        verbose=False,
    )
    return float(result.mauve)


# ──────────────────────────────────────────────
# Runner
# ──────────────────────────────────────────────

def evaluate_all(
    input_path: str,
    output_path: str,
    compute_mauve: bool = False,
):
    """
    Run all evaluation metrics on cited responses.

    Args:
        input_path:    Path to cited responses JSON (from Step 4).
        output_path:   Path to save evaluation results.
        compute_mauve: Whether to compute MAUVE (requires mauve-text).
    """
    with open(input_path, "r") as f:
        data = json.load(f)

    per_example = []
    all_predictions = []
    all_references = []

    for example in data:
        cited_response = example.get("cited_response", "")
        matched_claims = example.get("matched_claims", [])
        ex_metrics = {}

        # Citation Precision — claim level
        ex_metrics["citation_precision"] = citation_precision_nli(matched_claims)

        # Citation Recall — claim level
        ex_metrics["citation_recall"] = citation_recall_nli(matched_claims)

        # Correctness — Exact Match (if gold answers available)
        gold_answers = example.get("gold_answers", [])
        if gold_answers:
            ex_metrics["correctness_em"] = correctness_exact_match(
                cited_response, gold_answers
            )

        # Correctness — Claim Recall (if gold claims available)
        gold_claims = example.get("gold_claims", [])
        if gold_claims:
            ex_metrics["correctness_claim_recall"] = correctness_claim_recall(
                cited_response, gold_claims
            )

        per_example.append({
            "question": example.get("question", ""),
            "metrics": ex_metrics,
        })

        all_predictions.append(cited_response)
        if "raw_response" in example:
            all_references.append(example["raw_response"])

    # Aggregate means
    metric_keys = set()
    for ex in per_example:
        metric_keys.update(ex["metrics"].keys())

    aggregated = {}
    for key in sorted(metric_keys):
        values = [ex["metrics"][key] for ex in per_example if key in ex["metrics"]]
        if values:
            aggregated[key] = float(np.mean(values))

    # MAUVE (corpus-level, optional)
    if compute_mauve and all_predictions and all_references:
        try:
            aggregated["fluency_mauve"] = fluency_mauve(
                all_predictions, all_references
            )
        except Exception as e:
            print(f"Warning: MAUVE computation failed: {e}")

    results = {
        "num_examples": len(data),
        "metrics": aggregated,
        "per_example": per_example,
    }

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
    parser.add_argument("--compute-mauve", action="store_true",
                        help="Compute MAUVE fluency (requires mauve-text)")
    args = parser.parse_args()
    evaluate_all(args.input, args.output, args.compute_mauve)