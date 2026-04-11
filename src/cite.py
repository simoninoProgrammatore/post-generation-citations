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
    return re.split(r'(?<=[.!?])(?:\[\d+\])*\s+', text.strip())


def insert_citations(
    response: str,
    matched_claims: list[dict],
    citation_map: dict,
    remove_unsupported: bool = False,
) -> tuple[str, list[dict]]:
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

    stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on',
                 'at', 'to', 'for', 'of', 'and', 'or', 'but', 'with', 'as',
                 'his', 'her', 'their', 'its', 'has', 'have', 'had', 'by',
                 'it', 'this', 'that', 'from', 'not', 'be', 'been'}

    sentences = _sentence_split(response)
    cited_sentences = []

    for sentence in sentences:
        sent_words = set(re.sub(r'[^\w\s]', '', sentence.lower()).split()) - stopwords
        citation_nums: set[int] = set()

        # Calcola overlap per ogni claim
        scored_claims = []
        for claim_text, nums in claim_to_citations.items():
            claim_words = set(re.sub(r'[^\w\s]', '', claim_text.lower()).split()) - stopwords
            if not claim_words:
                continue
            overlap = len(claim_words & sent_words) / len(claim_words)
            if overlap >= 0.5:
                scored_claims.append((overlap, nums))

        # Best match: prendi solo i claim nel top tier (entro 0.15 dal migliore)
        if scored_claims:
            scored_claims.sort(key=lambda x: x[0], reverse=True)
            top_overlap = scored_claims[0][0]
            for overlap, nums in scored_claims:
                if overlap >= top_overlap - 0.15:
                    citation_nums.update(nums)

        if citation_nums:
            markers = "".join(f"[{n}]" for n in sorted(citation_nums))
            cited_sentences.append(f"{sentence}{markers}")
        elif remove_unsupported:
            pass
        else:
            cited_sentences.append(sentence)

    cited_response = " ".join(cited_sentences)

    all_passages = []
    for mc in matched_claims:
        all_passages.extend(mc["supporting_passages"])

    reference_list = build_reference_list(citation_map, all_passages)

    return cited_response, reference_list


def build_reference_list(citation_map: dict, passages: list[dict]) -> list[dict]:
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