#!/bin/bash

echo "✅ Running docker_entrypoint.sh ..."

# ---------------------------------------------------
# Set environment variables
# ---------------------------------------------------

export USER=root
export PYTHONDONTWRITEBYTECODE=1
export HF_HOME=/workspace/SongGeneration/
export NCCL_HOME=/usr/local/tccl
export PYTHONPATH="/workspace/repo/songgeneration/codeclm/tokenizer/:/workspace/repo/songgeneration:/workspace/repo/songgeneration/codeclm/tokenizer/Flow1dVAE/:/workspace/repo/songgeneration/codeclm/tokenizer/:$PYTHONPATH"

echo "✅ Environment variables set."
echo ""
echo "  USER = ${USER}"
echo "  PYTHONDONTWRITEBYTECODE = ${PYTHONDONTWRITEBYTECODE}"
echo "  HF_HOME  = ${HF_HOME}"
echo "  NCCL_HOME  = ${NCCL_HOME}"
echo "  PYTHONPATH  = ${PYTHONPATH}"
echo ""

# ---------------------------------------------------
# Check if repo exists
# ---------------------------------------------------

if [ ! -d "/workspace/repo/songgeneration/.git" ]; then
    echo "🚀 Cloning repo into /workspace/repo/songgeneration ..."
    mkdir -p /workspace/repo
    git clone https://github.com/AndrewYukon/songgeneration /workspace/repo/songgeneration
else
    echo "✅ Repo already exists at /workspace/repo/songgeneration"
fi

# ---------------------------------------------------
# Create required directories
# ---------------------------------------------------

mkdir -p /workspace/SongGeneration/jsonl
mkdir -p /workspace/SongGeneration/output

# ---------------------------------------------------
# Create symlinks
# ---------------------------------------------------

ln -sf /workspace/SongGeneration/ckpt /workspace/repo/songgeneration/ckpt
ln -sf /workspace/SongGeneration/third_party /workspace/repo/songgeneration/third_party
ln -sf /workspace/SongGeneration/jsonl /workspace/repo/songgeneration/jsonl
ln -sf /workspace/SongGeneration/output /workspace/repo/songgeneration/output

echo "✅ Directories and symlinks prepared."

# ---------------------------------------------------
# Handle optional arguments
# ---------------------------------------------------

CKPT_PATH=$1
JSONL=$2
SAVE_DIR=$3

echo ""
echo "------------------------------------------------------------"
echo "✨ Docker container is ready!"
echo ""
echo "✅ Environment:"
echo "  CKPT_PATH = ${CKPT_PATH}"
echo "  JSONL     = ${JSONL}"
echo "  SAVE_DIR  = ${SAVE_DIR}"
echo ""
echo "👉 To generate songs, run the following command:"
echo ""
echo "python3 generate.py \$CKPT_PATH \$JSONL \$SAVE_DIR"
echo ""
echo "Example:"
echo "python3 generate.py /workspace/SongGeneration/ckpt /workspace/SongGeneration/jsonl/test.jsonl /workspace/SongGeneration/output"
echo "------------------------------------------------------------"

# Switch to repo workdir
cd /workspace/repo/songgeneration

if [ $# -eq 0 ]; then
    echo "✅ docker_entrypoint.sh finished, keeping container alive..."
    exec tail -f /dev/null
else
    exec "$@"
fi