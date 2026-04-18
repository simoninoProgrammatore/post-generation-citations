"""
Download ALCE benchmark data (ASQA, QAMPARI, ELI5).
Source: https://github.com/princeton-nlp/ALCE

Usage:
    python scripts/download_data.py
"""

import os
import tarfile
import shutil


def main():
    data_dir = os.path.join("data", "alce")
    os.makedirs(data_dir, exist_ok=True)

    print("=" * 60)
    print("Downloading ALCE benchmark data")
    print("Datasets: ASQA, QAMPARI, ELI5")
    print("=" * 60)
    print()

    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("huggingface_hub not installed. Installing...")
        os.system("pip install huggingface-hub")
        from huggingface_hub import hf_hub_download

    try:
        print("Downloading from HuggingFace...")
        tar_path = hf_hub_download(
            repo_id="princeton-nlp/ALCE-data",
            filename="ALCE-data.tar",
            repo_type="dataset",
            local_dir=data_dir,
        )

        print(f"Downloaded to: {tar_path}")
        print("Extracting...")

        with tarfile.open(tar_path, "r") as tar:
            tar.extractall(path=data_dir)

        # Move files from ALCE-data subfolder to data/alce/
        extracted_dir = os.path.join(data_dir, "ALCE-data")
        if os.path.exists(extracted_dir):
            for item in os.listdir(extracted_dir):
                src = os.path.join(extracted_dir, item)
                dst = os.path.join(data_dir, item)
                if os.path.exists(dst):
                    if os.path.isdir(dst):
                        shutil.rmtree(dst)
                    else:
                        os.remove(dst)
                shutil.move(src, dst)
            shutil.rmtree(extracted_dir)

        # Clean up
        if os.path.exists(tar_path):
            os.remove(tar_path)
        hf_cache = os.path.join(data_dir, ".huggingface")
        if os.path.exists(hf_cache):
            shutil.rmtree(hf_cache)

    except Exception as e:
        print(f"Error: {e}")
        print()
        print("Download manually from:")
        print("https://huggingface.co/datasets/princeton-nlp/ALCE-data")
        return

    # Show results
    print()
    print("=" * 60)
    print("Download complete! Contents:")
    print("=" * 60)

    for item in sorted(os.listdir(data_dir)):
        item_path = os.path.join(data_dir, item)
        if os.path.isfile(item_path):
            size_mb = os.path.getsize(item_path) / (1024 * 1024)
            print(f"  {item} ({size_mb:.1f} MB)")
        elif os.path.isdir(item_path):
            print(f"  {item}/")

    print()
    for dataset in ["asqa", "qampari", "eli5"]:
        found = [f for f in os.listdir(data_dir) if dataset in f.lower()]
        if found:
            print(f"  OK  {dataset.upper()}: {', '.join(found)}")
        else:
            print(f"  --  {dataset.upper()}: not found")

    print()
    print("Ready!")


if __name__ == "__main__":
    main()