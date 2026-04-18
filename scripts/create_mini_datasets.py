"""
Create mini versions of ALCE datasets for quick testing.
Takes the first 5 examples from each dataset (ASQA, QAMPARI, ELI5).

Usage:
    python scripts/create_mini_datasets.py
"""

import json
import os
import glob


def crop_dataset(input_path, output_path, n=5):
    """Load a JSON dataset and save only the first n examples."""
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        cropped = data[:n]
    elif isinstance(data, dict):
        # Some ALCE files are dicts with a list inside
        for key, value in data.items():
            if isinstance(value, list) and len(value) > n:
                data[key] = value[:n]
        cropped = data
    else:
        print(f"  Skipping {input_path}: unexpected format")
        return

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cropped, f, indent=2, ensure_ascii=False)

    count = len(cropped) if isinstance(cropped, list) else "dict"
    size_kb = os.path.getsize(output_path) / 1024
    print(f"  {os.path.basename(output_path)} -> {count} examples ({size_kb:.0f} KB)")


def main():
    # Where the full ALCE data lives
    source_dir = os.path.join("data", "alce", "ALCE-data")
    
    # Fallback: maybe data is directly in data/alce/
    if not os.path.exists(source_dir):
        source_dir = os.path.join("data", "alce")

    if not os.path.exists(source_dir):
        print("ERROR: Cannot find ALCE data.")
        print("Expected at: data/alce/ALCE-data/ or data/alce/")
        print("Run 'python scripts/download_data.py' first.")
        return

    # Output directory for mini datasets
    mini_dir = os.path.join("data", "alce_mini")
    os.makedirs(mini_dir, exist_ok=True)

    print("=" * 60)
    print("Creating mini ALCE datasets (5 examples each)")
    print(f"Source: {source_dir}")
    print(f"Output: {mini_dir}")
    print("=" * 60)
    print()

    # Find all JSON files
    json_files = glob.glob(os.path.join(source_dir, "*.json"))
    json_files += glob.glob(os.path.join(source_dir, "**", "*.json"), recursive=True)
    
    # Remove duplicates and sort
    json_files = sorted(set(json_files))

    if not json_files:
        print("No JSON files found in source directory.")
        print(f"Contents of {source_dir}:")
        for item in os.listdir(source_dir):
            print(f"  {item}")
        return

    print(f"Found {len(json_files)} JSON files:")
    print()

    for json_file in json_files:
        rel_path = os.path.relpath(json_file, source_dir)
        output_path = os.path.join(mini_dir, rel_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            crop_dataset(json_file, output_path, n=5)
        except Exception as e:
            print(f"  Error processing {rel_path}: {e}")

    print()
    print("=" * 60)
    print("Done! Mini datasets saved in data/alce_mini/")
    print("Use these for quick pipeline testing.")
    print("=" * 60)


if __name__ == "__main__":
    main()