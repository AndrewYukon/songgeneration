#!/bin/bash

echo "✅ Running docker_entrypoint.sh ..."

# ---------------------------------------------------
# Set environment variables
# ---------------------------------------------------

export USER=root
export PYTHONDONTWRITEBYTECODE=1
#export TRANSFORMERS_CACHE="$(pwd)/third_party/hub"
export HF_HOME=/workspace/SongGeneration/
export NCCL_HOME=/usr/local/tccl
export NCCL_HOME="$(pwd)/codeclm/tokenizer/:$(pwd):$(pwd)/codeclm/tokenizer/Flow1dVAE/:$(pwd)/codeclm/tokenizer/:$PYTHONPATH"

echo "✅ Environment variables set."
echo ""
echo "✅ Environment:"
echo "  USER = ${USER}"
echo "  PYTHONDONTWRITEBYTECODE = ${PYTHONDONTWRITEBYTECODE}"
echo "  HF_HOME  = ${HF_HOME}"
echo "  NCCL_HOME  = ${NCCL_HOME}"
echo "  NCCL_HOME  = ${NCCL_HOME}"
echo ""

# ---------------------------------------------------
# Create required directories
# ---------------------------------------------------

mkdir -p /workspace/SongGeneration/jsonl
mkdir -p /workspace/SongGeneration/output

# ---------------------------------------------------
# Create symlinks
# ---------------------------------------------------

ln -sf /workspace/SongGeneration/ckpt /repo/songgeneration/ckpt
ln -sf /workspace/SongGeneration/third_party /repo/songgeneration/third_party
ln -sf /workspace/SongGeneration/jsonl /repo/songgeneration/jsonl
ln -sf /workspace/SongGeneration/output /repo/songgeneration/output

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

# Start an interactive shell
# exec /bin/bash

# keep container running
echo "✅ docker_entrypoint.sh finished, keeping container alive."
exec tail -f /dev/null
