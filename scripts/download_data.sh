#!/bin/bash
# Download ALCE benchmark data
# Source: https://github.com/princeton-nlp/ALCE

set -e

DATA_DIR="data/alce"
mkdir -p "$DATA_DIR"

echo "=== Downloading ALCE benchmark data ==="
echo ""

# Clone ALCE repo (sparse checkout for data only)
if [ ! -d "$DATA_DIR/.alce_repo" ]; then
    echo "Cloning ALCE repository..."
    git clone --depth 1 https://github.com/princeton-nlp/ALCE.git "$DATA_DIR/.alce_repo"
else
    echo "ALCE repository already cloned."
fi

# Copy relevant data files
echo "Copying dataset files..."
cp -r "$DATA_DIR/.alce_repo/data/"* "$DATA_DIR/" 2>/dev/null || true

echo ""
echo "=== Download complete ==="
echo "Data saved to: $DATA_DIR"
echo ""
echo "Available datasets:"
ls -la "$DATA_DIR/" 2>/dev/null || echo "  (check the ALCE repo for data download instructions)"
echo ""
echo "NOTE: Some ALCE data files may need to be downloaded separately."
echo "See https://github.com/princeton-nlp/ALCE#data for details."
