#!/usr/bin/env python3
import sys
import os
import subprocess

def run_generate(ckpt_path, jsonl_path, save_dir):
    print("✅ Running run_generate.py ...")

    print("\n✨ Using parameters:")
    print(f"  CKPT_PATH = {ckpt_path}")
    print(f"  JSONL     = {jsonl_path}")
    print(f"  SAVE_DIR  = {save_dir}")

    # Check paths
    if not os.path.exists(ckpt_path):
        print(f"❌ ERROR: CKPT_PATH not found: {ckpt_path}")
        sys.exit(1)

    if not os.path.exists(jsonl_path):
        print(f"⚠️  JSONL directory not found. Creating it: {jsonl_path}")
        os.makedirs(jsonl_path, exist_ok=True)

    if not os.path.exists(save_dir):
        print(f"⚠️  SAVE_DIR directory not found. Creating it: {save_dir}")
        os.makedirs(save_dir, exist_ok=True)

    # Build the command
    cmd = [
        "python3",
        "generate.py",
        ckpt_path,
        jsonl_path,
        save_dir
    ]

    print("\n🚀 Running command:")
    print(" ".join(cmd))
    print()

    # Run generate.py
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ generate.py failed with error code: {e.returncode}")
        sys.exit(1)

    print("\n✅ generate.py finished successfully!")


if __name__ == "__main__":
    # Default paths
    default_ckpt_path = "/workspace/SongGeneration/ckpt"
    default_jsonl = "/workspace/SongGeneration/jsonl/test.jsonl"
    default_save_dir = "/workspace/SongGeneration/output"

    # Read optional arguments
    ckpt_path = sys.argv[1] if len(sys.argv) > 1 else default_ckpt_path
    jsonl_path = sys.argv[2] if len(sys.argv) > 2 else default_jsonl
    save_dir = sys.argv[3] if len(sys.argv) > 3 else default_save_dir

    # Change to project directory
    os.chdir("/repo/songgeneration")

    run_generate(ckpt_path, jsonl_path, save_dir)