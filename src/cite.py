"""
Step 4: Insert inline citations into the generated response.

Given matched claims and their supporting passages, this module 
reconstructs the response with inline citation markers (e.g., [1][2]).
"""

import re
import json
import argparse
from pathlib import Path


def build_citation_map(matched_claims: list[dict]) -> dict:
    """
    Build a mapping from passage IDs to citation numbers.

    Args:
        matched_claims: List of claims with their supporting passages.

    Returns:
        A dict mapping passage_id -> citation_number (1-indexed).
    """
    citation_map = {}
    counter = 1

    for mc in matched_claims:
        for passage in mc["supporting_passages"]:
            pid = passage.get("id") or passage.get("title", "")
            if pid not in citation_map:
                citation_map[pid] = counter
                counter += 1

    return citation_map


def _sentence_split(text: str) -> list[str]:
    """Split text into sentences, preserving trailing whitespace."""
    return re.split(r'(?<=[.!?])\s+', text.strip())


def insert_citations(
    response: str,
    matched_claims: list[dict],
    citation_map: dict,
    remove_unsupported: bool = False,
) -> tuple[str, list[dict]]:
    """
    Insert inline citations into the response text.

    Strategy:
      1. Split the response into sentences.
      2. For each sentence, find which claims it contains (substring match).
      3. Collect the citation numbers for those claims.
      4. Append citation markers (e.g. [1][2]) after the sentence.
      5. Build a reference list for all cited passages.

    Args:
        response:          Original response text.
        matched_claims:    Claims with supporting passages.
        citation_map:      Mapping from passage ID to citation number.
        remove_unsupported: If True, drop sentences with no citations.

    Returns:
        Tuple of (cited_response, reference_list).
    """
    # Build a quick lookup: claim text -> list of citation numbers
    claim_to_citations: dict[str, list[int]] = {}
    for mc in matched_claims:
        claim_text = mc["claim"]
        nums = []
        for passage in mc["supporting_passages"]:
            pid = passage.get("id") or passage.get("title", "")
            if pid in citation_map:
                nums.append(citation_map[pid])
        if nums:
            claim_to_citations[claim_text] = sorted(set(nums))

    sentences = _sentence_split(response)
    cited_sentences = []

    for sentence in sentences:
        sentence_lower = sentence.lower()
        citation_nums: set[int] = set()

        for claim_text, nums in claim_to_citations.items():
            # Check if any meaningful fragment of the claim appears in the sentence
            # (use the first 60 chars as a fingerprint to handle minor wording diffs)
            fragment = claim_text[:60].lower().rstrip(".,;")
            if fragment and fragment in sentence_lower:
                citation_nums.update(nums)

        if citation_nums:
            markers = "".join(f"[{n}]" for n in sorted(citation_nums))
            cited_sentences.append(f"{sentence}{markers}")
        elif remove_unsupported:
            pass  # drop sentence
        else:
            cited_sentences.append(sentence)

    cited_response = " ".join(cited_sentences)

    # Collect all passages referenced at least once
    all_passages = []
    for mc in matched_claims:
        all_passages.extend(mc["supporting_passages"])

    reference_list = build_reference_list(citation_map, all_passages)

    return cited_response, reference_list


def build_reference_list(citation_map: dict, passages: list[dict]) -> list[dict]:
    """
    Build the reference list to append to the response.

    Returns:
        List of references with citation number, title, and text.
    """
    references = []
    pid_to_passage = {p.get("id", p.get("title", "")): p for p in passages}

    for pid, num in sorted(citation_map.items(), key=lambda x: x[1]):
        passage = pid_to_passage.get(pid, {})
        references.append({
            "citation_number": num,
            "title": passage.get("title", ""),
            "text": passage.get("text", ""),
        })

    return references


def run(input_path: str, output_path: str, remove_unsupported: bool = False):
    """
    Insert citations into all responses.

    Args:
        input_path:        Path to matched claims JSON (from Step 3).
        output_path:       Path to save cited responses.
        remove_unsupported: Whether to remove unsupported claims.
    """
    with open(input_path, "r") as f:
        data = json.load(f)

    for example in data:
        citation_map = build_citation_map(example["matched_claims"])
        cited_response, references = insert_citations(
            example["raw_response"],
            example["matched_claims"],
            citation_map,
            remove_unsupported,
        )
        example["cited_response"] = cited_response
        example["references"] = references

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Inserted citations in {len(data)} responses -> {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Insert citations")
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, default="results/cited.json")
    parser.add_argument("--remove-unsupported", action="store_true")
    args = parser.parse_args()
    run(args.input, args.output, args.remove_unsupported)