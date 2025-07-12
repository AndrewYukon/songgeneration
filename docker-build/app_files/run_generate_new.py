#docker-build/app_files/run_generate.py
#!/usr/bin/env python3
import sys
import os
import subprocess
import argparse

def run_generate(args):
    print("✅ Running run_generate.py ...")

    print("\n✨ Using parameters:")
    for k, v in vars(args).items():
        print(f"  {k.upper()} = {v}")

    if not os.path.exists(args.ckpt_path):
        print(f"❌ ERROR: CKPT_PATH not found: {args.ckpt_path}")
        sys.exit(1)

    if not os.path.exists(args.jsonl_path):
        print(f"⚠️  JSONL not found. Creating directory for it: {os.path.dirname(args.jsonl_path)}")
        os.makedirs(os.path.dirname(args.jsonl_path), exist_ok=True)

    if os.path.exists(args.save_dir):
        print(f"⚠️  SAVE_DIR exists. Removing old contents...")
        import shutil
        shutil.rmtree(args.save_dir)

    os.makedirs(args.save_dir, exist_ok=True)

    cmd = [
        "python3",
        "generate_new.py",
        args.ckpt_path,
        args.jsonl_path,
        args.save_dir,
    ]

    cmd += ["--cfg_coef", str(args.cfg_coef)]
    cmd += ["--temperature", str(args.temperature)]
    cmd += ["--top_k", str(args.top_k)]
    cmd += ["--top_p", str(args.top_p)]
    if args.record_tokens:
        cmd += ["--record_tokens"]
    cmd += ["--record_window", str(args.record_window)]
    if args.duration is not None:
        cmd += ["--duration", str(args.duration)]

    print("\n🚀 Running command:")
    print(" ".join(cmd))
    print()

    subprocess.run(cmd, check=True)

    print("\n✅ generate.py finished successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ckpt_path", type=str, default="/workspace/SongGeneration/ckpt")
    parser.add_argument("--jsonl_path", type=str, default="/workspace/SongGeneration/jsonl/test.jsonl")
    parser.add_argument("--save_dir", type=str, default="/workspace/SongGeneration/output")
    parser.add_argument("--cfg_coef", type=float, default=1.5)
    parser.add_argument("--temperature", type=float, default=0.9)
    parser.add_argument("--top_k", type=int, default=50)
    parser.add_argument("--top_p", type=float, default=0.0)
    parser.add_argument("--record_tokens", action="store_true")
    parser.add_argument("--record_window", type=int, default=50)
    parser.add_argument("--duration", type=float, default=None)

    args = parser.parse_args()

    os.chdir("/repo/songgeneration")
    run_generate(args)