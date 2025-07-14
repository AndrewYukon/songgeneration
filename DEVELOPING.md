----------------------
在runpod上：测试脚本：：：
----------------------

cd /workspace/repo/songgeneration

nohup python3.10 generate_new.py \
    ckpt \
    ./sample/test.jsonl \
    ./output \
    --cfg_coef 1.2 \
    --temperature 0.7 \
    --top_k 50 \
    --top_p 0.9 \
    --duration 300 \
    2>&1 | awk '{ print strftime("[%Y-%m-%d %H:%M:%S]"), $0; fflush() }' | tee /workspace/SongGeneration/output/audios/generate.log &


nohup python3.10 generate_new.py \
    ckpt \
    ./sample/test.jsonl \
    ./output \
    --temperature 0.7 \
    2>&1 | tee /workspace/SongGeneration/output/audios/generate.log &