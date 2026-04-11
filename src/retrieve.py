"""
Step 3: Match atomic claims to supporting evidence passages.

Given a list of claims and a pool of candidate passages (provided 
by ALCE), this module determines which passages support each claim.
"""

import json
import argparse
from pathlib import Path
from functools import lru_cache


# ──────────────────────────────────────────────
# Evidence extraction
# ──────────────────────────────────────────────

def extract_evidence(claim: str, passage_text: str, model: str = "claude-haiku-4-5-20251001") -> dict:
    """
    Given a matched claim and passage, extract the exact supporting sentence
    and a short summary explaining the support.

    Args:
        claim:        The atomic claim to verify.
        passage_text: Full text of the matched passage.
        model:        LLM to use for extraction.

    Returns:
        Dict with 'extraction' (verbatim from passage) and 'summary'.
    """
    from llm_client import call_llm_json

    prompt = f"""You are a strict fact-checking assistant.

Claim: "{claim}"

Passage:
\"\"\"{passage_text}\"\"\"

Find the exact sentence(s) in the passage that DIRECTLY support the claim.
The sentence must contain the same factual information as the claim, not just related information.

For example:
- Claim: "The iPhone was called 'iPhone' at release"
- BAD extraction: "The iPhone was released on June 29, 2007" (related but different fact)
- GOOD extraction: "it was simply called iPhone" (directly supports the naming claim)

Return ONLY a JSON object:
{{
  "extraction": "the exact sentence(s) copied verbatim from the passage",
  "summary": "one-sentence summary of why this supports the claim"
}}

If no sentence DIRECTLY supports the specific fact in the claim, you MUST return:
{{"extraction": "", "summary": "No direct support found."}}
"""
    try:
        result = call_llm_json(prompt, model=model)
        return {
            "extraction": result.get("extraction", ""),
            "summary": result.get("summary", ""),
        }
    except Exception:
        return {"extraction": "", "summary": ""}


# ──────────────────────────────────────────────
# NLI-based matching
# ──────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_nli_model(model_name: str):
    from sentence_transformers import CrossEncoder
    return CrossEncoder(model_name)


def match_with_nli(
    claim: str,
    passages: list[dict],
    model_name: str = "cross-encoder/nli-deberta-v3-large",
    threshold: float = 0.5,
    top_k: int = 3,
) -> list[dict]:
    if not passages:
        return []

    model = _load_nli_model(model_name)
    pairs = [(p["text"], claim) for p in passages]
    scores = model.predict(pairs)

    import numpy as np

    def softmax(x):
        e = np.exp(x - np.max(x, axis=1, keepdims=True))
        return e / e.sum(axis=1, keepdims=True)

    entailment_scores = softmax(scores)[:, 1]

    results = []
    for i, score in enumerate(entailment_scores):
        if score >= threshold:
            results.append({**passages[i], "entailment_score": float(score)})

    results.sort(key=lambda x: x["entailment_score"], reverse=True)
    return results[:top_k]


# ──────────────────────────────────────────────
# Similarity-based matching (baseline)
# ──────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_embedding_model(model_name: str):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_name)


def match_with_similarity(
    claim: str,
    passages: list[dict],
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    top_k: int = 3,
) -> list[dict]:
    if not passages:
        return []

    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity

    model = _load_embedding_model(model_name)
    claim_emb = model.encode([claim])
    passage_embs = model.encode([p["text"] for p in passages])
    sims = cosine_similarity(claim_emb, passage_embs)[0]

    ranked = sorted(enumerate(sims), key=lambda x: x[1], reverse=True)[:top_k]
    return [{**passages[i], "similarity_score": float(score)} for i, score in ranked]


# ──────────────────────────────────────────────
# LLM-based matching (Claude re-ranker)
# ──────────────────────────────────────────────

def match_with_llm(
    claim: str,
    passages: list[dict],
    threshold: float = 0.5,
    top_k: int = 3,
) -> list[dict]:
    from llm_client import call_llm_json

    if not passages:
        return []

    # Step 1: pre-filtra con similarity → top 10
    candidates = match_with_similarity(claim, passages, top_k=10)
    if not candidates:
        return []

    # Step 2: Claude re-ranking
    passages_text = "\n\n".join([
        f"[{i}] {p.get('title', 'N/A')}: {p.get('text', '')[:500]}"
        for i, p in enumerate(candidates)
    ])

    prompt = f"""You are a fact-checking assistant.

Claim: "{claim}"

For each passage below, decide if it SUPPORTS the claim (entails it), CONTRADICTS it, or is NEUTRAL.
Return ONLY a JSON array like:
[{{"idx": 0, "label": "supports", "score": 0.95}}, ...]

Passages:
{passages_text}
"""

    try:
        results = call_llm_json(prompt)
    except Exception:
        return candidates[:top_k]

    scored = []
    for r in results:
        idx = r.get("idx")
        if (
            isinstance(idx, int)
            and 0 <= idx < len(candidates)
            and r.get("label") == "supports"
            and r.get("score", 0) >= threshold
        ):
            p = candidates[idx]
            scored.append({**p, "entailment_score": float(r["score"])})

    scored.sort(key=lambda x: x["entailment_score"], reverse=True)
    return scored[:top_k]


# ──────────────────────────────────────────────
# Runner
# ──────────────────────────────────────────────

def run(input_path: str, output_path: str, method: str = "nli", extract: bool = True):
    """
    Match claims to evidence passages and optionally extract
    the exact supporting sentence from each passage.

    Args:
        input_path:  Path to claims JSON (from Step 2).
        output_path: Path to save matched claims.
        method:      Matching method ('nli', 'similarity', 'llm').
        extract:     If True, run LLM extraction on each match.
    """
    with open(input_path, "r") as f:
        data = json.load(f)

    match_fn = {
        "nli": match_with_nli,
        "similarity": match_with_similarity,
        "llm": match_with_llm,
    }[method]

    for example in data:
        passages = example.get("passages", [])
        matched_claims = []

        for claim in example["claims"]:
            matches = match_fn(claim, passages)

            if extract:
                for match in matches:
                    ev = extract_evidence(claim, match.get("text", ""))
                    match["extraction"] = ev["extraction"]
                    match["summary"] = ev["summary"]

                # Gate: scarta match senza evidenza concreta
                matches = [m for m in matches if m.get("extraction", "").strip()]

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
    parser.add_argument("--method", type=str, default="nli", choices=["nli", "similarity", "llm"])
    parser.add_argument("--no-extract", action="store_true",
                        help="Skip LLM evidence extraction")
    args = parser.parse_args()
    run(args.input, args.output, args.method, extract=not args.no_extract)