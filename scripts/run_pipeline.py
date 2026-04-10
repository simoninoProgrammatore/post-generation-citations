"""
Run the full post-generation citation pipeline.

Usage:
    python scripts/run_pipeline.py --dataset asqa --model gpt-4
    python scripts/run_pipeline.py --dataset asqa --steps decompose,retrieve,cite,evaluate
"""

import argparse
import yaml
from pathlib import Path


def load_config(config_path: str = "config/default.yaml") -> dict:
    """Load pipeline configuration from YAML."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Run post-generation citation pipeline")
    parser.add_argument("--config", type=str, default="config/default.yaml")
    parser.add_argument("--dataset", type=str, default=None, help="Override dataset name")
    parser.add_argument("--model", type=str, default=None, help="Override generation model")
    parser.add_argument(
        "--steps", type=str, default="generate,decompose,retrieve,cite,evaluate",
        help="Comma-separated list of pipeline steps to run"
    )
    args = parser.parse_args()

    config = load_config(args.config)

    # Override config with CLI args
    if args.dataset:
        config["dataset"]["name"] = args.dataset
    if args.model:
        config["generation"]["model"] = args.model

    steps = args.steps.split(",")
    output_dir = Path(config["output"]["dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Post-Generation Citation Pipeline")
    print("=" * 60)
    print(f"  Dataset:  {config['dataset']['name']}")
    print(f"  Model:    {config['generation']['model']}")
    print(f"  Steps:    {', '.join(steps)}")
    print(f"  Output:   {output_dir}")
    print("=" * 60)
    print()

    # Step 1: Generate
    if "generate" in steps:
        print("[Step 1/5] Generating responses...")
        from src.generate import run as generate_run
        generate_run(
            dataset_path=f"{config['dataset']['data_dir']}/{config['dataset']['name']}.json",
            output_path=str(output_dir / "generations.json"),
            model=config["generation"]["model"],
        )
        print()

    # Step 2: Decompose
    if "decompose" in steps:
        print("[Step 2/5] Decomposing into atomic claims...")
        from src.decompose import run as decompose_run
        decompose_run(
            input_path=str(output_dir / "generations.json"),
            output_path=str(output_dir / "claims.json"),
            method=config["decomposition"]["method"],
        )
        print()

    # Step 3: Retrieve / Match
    if "retrieve" in steps:
        print("[Step 3/5] Matching claims to evidence...")
        from src.retrieve import run as retrieve_run
        retrieve_run(
            input_path=str(output_dir / "claims.json"),
            output_path=str(output_dir / "matched.json"),
            method=config["retrieval"]["method"],
        )
        print()

    # Step 4: Cite
    if "cite" in steps:
        print("[Step 4/5] Inserting citations...")
        from src.cite import run as cite_run
        cite_run(
            input_path=str(output_dir / "matched.json"),
            output_path=str(output_dir / "cited.json"),
            remove_unsupported=config["citation"]["remove_unsupported"],
        )
        print()

    # Step 5: Evaluate
    if "evaluate" in steps:
        print("[Step 5/5] Evaluating...")
        from src.evaluate import run as evaluate_run
        evaluate_run(
            input_path=str(output_dir / "cited.json"),
            output_path=str(output_dir / "evaluation.json"),
        )
        print()

    print("=" * 60)
    print("Pipeline complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
