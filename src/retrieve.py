"""
Step 3: Match atomic claims to supporting evidence passages.

Given a list of claims and a pool of candidate passages (provided 
by ALCE), this module determines which passages support each claim.
"""

import re
import json
import argparse
from pathlib import Path
from functools import lru_cache


# ──────────────────────────────────────────────
# Evidence extraction
# ──────────────────────────────────────────────

def extract_evidence(claim: str, passage_text: str, model_name: str = "cross-encoder/nli-deberta-v3-large") -> dict:
    """
    Extract the sentence from the passage that best supports the claim,
    using NLI entailment scoring instead of LLM.
    """
    import numpy as np

    sentences = _split_passage_into_sentences(passage_text)
    if not sentences:
        return {"extraction": "", "extraction_start": -1, "summary": "No sentences found."}

    model = _load_nli_model(model_name)
    pairs = [(s, claim) for s in sentences]
    scores = model.predict(pairs)
    scores = np.array(scores)
    if scores.ndim == 1:
        scores = scores.reshape(1, -1)

    exp = np.exp(scores - np.max(scores, axis=1, keepdims=True))
    probs = exp / exp.sum(axis=1, keepdims=True)
    entailment_scores = probs[:, 1]

    best_idx = int(np.argmax(entailment_scores))
    best_score = float(entailment_scores[best_idx])
    best_sentence = sentences[best_idx]

    if best_score >= 0.5:
        start = passage_text.find(best_sentence)
        return {
            "extraction": best_sentence,
            "extraction_start": start,
            "summary": f"Entailment score: {best_score:.3f}",
        }

    return {"extraction": "", "extraction_start": -1, "summary": "No direct support found."}


# ──────────────────────────────────────────────
# Sentence splitting
# ──────────────────────────────────────────────

def _split_passage_into_sentences(text: str) -> list[str]:
    """
    Split a passage into individual sentences.
    
    Handles common abbreviations and edge cases to avoid
    bad splits on "U.S.", "Dr.", "Mr.", etc.
    """
    # Protect common abbreviations
    protected = text
    abbreviations = ["Mr.", "Mrs.", "Ms.", "Dr.", "Jr.", "Sr.", "Prof.",
                     "Inc.", "Ltd.", "Corp.", "vs.", "etc.", "approx.",
                     "U.S.", "U.K.", "E.U."]
    placeholders = {}
    for i, abbr in enumerate(abbreviations):
        placeholder = f"__ABBR{i}__"
        placeholders[placeholder] = abbr
        protected = protected.replace(abbr, placeholder)

    # Split on sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', protected.strip())

    # Restore abbreviations
    restored = []
    for sent in sentences:
        for placeholder, abbr in placeholders.items():
            sent = sent.replace(placeholder, abbr)
        sent = sent.strip()
        if sent:
            restored.append(sent)

    return restored


# ──────────────────────────────────────────────
# NLI model loading
# ──────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_nli_model(model_name: str):
    from sentence_transformers import CrossEncoder
    return CrossEncoder(model_name)


# ──────────────────────────────────────────────
# NLI-based matching (sentence-level)
# ──────────────────────────────────────────────

def match_with_nli(
    claim: str,
    passages: list[dict],
    model_name: str = "cross-encoder/nli-deberta-v3-large",
    threshold: float = 0.5,
    top_k: int = 3,
) -> list[dict]:
    """
    Match a claim against passages using NLI at sentence level.

    Instead of feeding entire passages to DeBERTa (which dilutes the
    entailment signal on long texts), each passage is split into 
    individual sentences. NLI is computed per (sentence, claim) pair
    and the maximum entailment score across all sentences is used as
    the passage score.

    This keeps DeBERTa within its training distribution (short premise,
    short hypothesis) and avoids false negatives on long passages.

    Args:
        claim:      The atomic claim to verify.
        passages:   List of candidate passages.
        model_name: NLI cross-encoder model.
        threshold:  Minimum entailment score.
        top_k:      Maximum passages to return.

    Returns:
        List of matching passages with entailment scores.
    """
    if not passages:
        return []

    import numpy as np

    model = _load_nli_model(model_name)

    # Build all (sentence, claim) pairs across all passages
    # Track which passage each pair belongs to
    all_pairs = []
    pair_to_passage = []  # index into passages list

    for p_idx, p in enumerate(passages):
        sentences = _split_passage_into_sentences(p.get("text", ""))
        if not sentences:
            continue
        for sent in sentences:
            all_pairs.append((sent, claim))
            pair_to_passage.append(p_idx)

    if not all_pairs:
        return []

    # Single batched predict for all pairs
    scores = model.predict(all_pairs)
    scores = np.array(scores)
    if scores.ndim == 1:
        scores = scores.reshape(1, -1)

    # Softmax per row → entailment probability (index 1)
    exp = np.exp(scores - np.max(scores, axis=1, keepdims=True))
    probs = exp / exp.sum(axis=1, keepdims=True)
    entailment_scores = probs[:, 1]

    # For each passage, take the max entailment score across its sentences
    passage_best_scores = {}
    for i, score in enumerate(entailment_scores):
        p_idx = pair_to_passage[i]
        if p_idx not in passage_best_scores or score > passage_best_scores[p_idx]:
            passage_best_scores[p_idx] = float(score)

    # Filter by threshold and build results
    results = []
    for p_idx, best_score in passage_best_scores.items():
        if best_score >= threshold:
            results.append({**passages[p_idx], "entailment_score": best_score})

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