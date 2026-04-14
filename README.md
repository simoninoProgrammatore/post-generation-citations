# Post-Generation Citation System

A post-generation attribution pipeline for Large Language Models. Given an LLM-generated response, the system decomposes it into atomic claims, retrieves supporting evidence, and inserts inline citations — all **after** generation.

This project is part of a Bachelor's thesis on evidence-based text generation with LLMs, following the post-generation paradigm described in [Schreieder et al. (2025)](https://arxiv.org/abs/2508.15396).

## Overview

```
Query ──► LLM ──► Raw Response ──► Decompose ──► Retrieve ──► Cite ──► Cited Response
                (pool retrieval)    (claims)    (evidence)   ([1][2])  (with citations)
```

### Pipeline Steps

1. **Generate** — An LLM produces a response to a query (citing ALCE passages).
2. **Decompose** — The response is broken into atomic claims (inspired by [FActScore](https://arxiv.org/abs/2305.14627), Min et al. 2023).
3. **Retrieve** — For each claim, matching evidence passages are found from the provided corpus.
4. **Cite** — Inline citations are inserted into the response, linking each claim to its supporting passage(s).
5. **Evaluate** — Citation quality is measured using the [ALCE](https://github.com/princeton-nlp/ALCE) benchmark metrics (Citation Precision/Recall NLI, Correctness, Fluency).

## Dataset

We use the **ALCE** benchmark (Gao et al., 2023), which provides three QA datasets with pre-retrieved passages from Wikipedia:

| Dataset | Description | Answer Type |
|---------|-------------|-------------|
| **ASQA** | Ambiguous factoid questions | Short-medium, multi-perspective |
| **QAMPARI** | Questions with many entity answers | List of entities |
| **ELI5** | Open-ended "Explain Like I'm 5" questions | Long-form explanatory |

Each example includes a query, pre-retrieved passages (5 or 100), and a gold answer with reference citations.

## Project Structure

```
post-generation-citations/
├── config/
│   └── default.yaml           # Pipeline configuration
├── data/
│   └── alce/                  # ALCE benchmark data (downloaded separately)
├── src/
│   ├── generate.py            # Step 1: LLM response generation
│   ├── decompose.py           # Step 2: Atomic claim decomposition
│   ├── retrieve.py            # Step 3: Claim-evidence matching
│   ├── cite.py                # Step 4: Citation insertion
│   └── evaluate.py            # Step 5: ALCE metrics evaluation
├── scripts/
│   ├── download_data.sh       # Download ALCE data
│   └── run_pipeline.py        # Run the full pipeline
├── notebooks/
│   └── exploration.ipynb      # Data exploration and analysis
├── results/                   # Experiment outputs
└── tests/                     # Unit tests
```

## Setup

```bash
# Clone the repository
git clone https://github.com/<your-username>/post-generation-citations.git
cd post-generation-citations

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Download ALCE data
bash scripts/download_data.sh
```

## Usage

```bash
# Run the full pipeline on ASQA
python scripts/run_pipeline.py --dataset asqa --model gpt-4

# Run individual steps
python -m src.generate --dataset asqa
python -m src.decompose --input results/generations.json
python -m src.retrieve --input results/claims.json
python -m src.cite --input results/matched.json
python -m src.evaluate --input results/cited.json
```

## Evaluation Metrics

Following the ALCE framework:

- **Citation Precision (NLI)** — Are the cited passages actually supporting the claims?
- **Citation Recall (NLI)** — Are all claims that should be cited actually cited?
- **Citation F1 (NLI)** — Harmonic mean of precision and recall.
- **Correctness** — Is the answer factually accurate? (Exact Match, Claim Recall)
- **Fluency** — Is the text natural and coherent? (MAUVE)

## References

- Schreieder, T., Schopf, T., & Färber, M. (2025). *Attribution, Citation, and Quotation: A Survey of Evidence-based Text Generation with Large Language Models*. arXiv:2508.15396.
- Gao, T., Yen, H., Yu, J., & Chen, D. (2023). *Enabling Large Language Models to Generate Text with Citations*. EMNLP 2023.
- Min, S., Krishna, K., Lyu, X., et al. (2023). *FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation*. EMNLP 2023.
- Gao, L., et al. (2023). *RARR: Researching and Revising What Language Models Say, Using Language Models*. ACL 2023.

## License

MIT
