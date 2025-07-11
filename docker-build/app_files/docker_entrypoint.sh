#!/bin/bash

echo "✅ Running docker_entrypoint.sh ..."

# 创建目录
mkdir -p /workspace/SongGeneration/jsonl
mkdir -p /workspace/SongGeneration/output

# 建立软链接
ln -sf /workspace/SongGeneration/ckpt /repo/songgeneration/ckpt
ln -sf /workspace/SongGeneration/third_party /repo/songgeneration/third_party
ln -sf /workspace/SongGeneration/jsonl /repo/songgeneration/jsonl
ln -sf /workspace/SongGeneration/output /repo/songgeneration/output

echo "✅ docker_entrypoint.sh completed."

# 保留 bash，进入交互
exec /bin/bash
