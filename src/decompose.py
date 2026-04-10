"""
Step 2: Decompose LLM responses into atomic claims.

Inspired by FActScore (Min et al., 2023), this module breaks a 
generated response into atomic facts — short statements that each 
contain one piece of information.

Example:
    Input:  "Earth derives its name from Old English and Germanic 
             words meaning 'ground', and it is the third planet 
             from the Sun."
    Output: ["Earth derives its name from Old English words",
             "Earth derives its name from Germanic words meaning ground",
             "Earth is the third planet from the Sun"]
"""

import json
import argparse
from pathlib import Path


def decompose_with_llm(text: str, model: str = "gpt-4") -> list[str]:
    """
    Decompose text into atomic claims using an LLM.
    
    Uses a prompt inspired by FActScore to break sentences 
    into independent atomic facts.
    
    Args:
        text: The response text to decompose.
        model: LLM to use for decomposition.
    
    Returns:
        A list of atomic claim strings.
    """
    # TODO: Implement LLM-based decomposition
    # Prompt template (from FActScore):
    # "Please breakdown the following sentence into independent facts:
    #  {sentence}"
    raise NotImplementedError("Implement claim decomposition.")


def decompose_with_sentences(text: str) -> list[str]:
    """
    Simple baseline: treat each sentence as a claim.
    
    This is less granular than atomic decomposition but 
    serves as a quick baseline.
    """
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def run(input_path: str, output_path: str, method: str = "llm"):
    """
    Decompose all generated responses into atomic claims.
    
    Args:
        input_path: Path to generations JSON (from Step 1).
        output_path: Path to save decomposed claims.
        method: Decomposition method ('llm' or 'sentences').
    """
    with open(input_path, "r") as f:
        data = json.load(f)

    decompose_fn = {
        "llm": decompose_with_llm,
        "sentences": decompose_with_sentences,
    }[method]

    for example in data:
        claims = decompose_fn(example["raw_response"])
        example["claims"] = claims

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    total_claims = sum(len(ex["claims"]) for ex in data)
    print(f"Decomposed {len(data)} responses into {total_claims} claims -> {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Decompose responses into claims")
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, default="results/claims.json")
    parser.add_argument("--method", type=str, default="llm", choices=["llm", "sentences"])
    args = parser.parse_args()
    run(args.input, args.output, args.method)
