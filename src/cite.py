"""
Step 4: Insert inline citations into the generated response.

Given matched claims and their supporting passages, this module 
reconstructs the response with inline citation markers (e.g., [1][2]).
"""

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


def insert_citations(
    response: str, 
    matched_claims: list[dict], 
    citation_map: dict,
    remove_unsupported: bool = False,
) -> tuple[str, list[dict]]:
    """
    Insert inline citations into the response text.
    
    Args:
        response: Original response text.
        matched_claims: Claims with supporting passages.
        citation_map: Mapping from passage ID to citation number.
        remove_unsupported: If True, remove claims without evidence.
    
    Returns:
        Tuple of (cited_response, reference_list).
    """
    # TODO: Implement citation insertion
    # Strategy:
    #   1. For each sentence in the response, find which claims it contains
    #   2. Collect citation numbers for those claims
    #   3. Append citation markers after the sentence
    #   4. Build a reference list at the end
    raise NotImplementedError("Implement citation insertion.")


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
        input_path: Path to matched claims JSON (from Step 3).
        output_path: Path to save cited responses.
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
