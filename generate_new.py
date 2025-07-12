#!/usr/bin/env python3
import sys
import os
import time
import json
import torch
import torchaudio
import numpy as np
import argparse
from omegaconf import OmegaConf

from codeclm.trainer.codec_song_pl import CodecLM_PL
from codeclm.models import CodecLM
from third_party.demucs.models.pretrained import get_model_from_yaml

# 可用的 Auto Prompt 类型
auto_prompt_type = [
    'Pop', 'R&B', 'Dance', 'Jazz', 'Folk', 'Rock', 
    'Chinese Style', 'Chinese Tradition', 'Metal', 
    'Reggae', 'Chinese Opera', 'Auto'
]

class Separator:
    def __init__(self, dm_model_path='third_party/demucs/ckpt/htdemucs.pth', dm_config_path='third_party/demucs/ckpt/htdemucs.yaml', gpu_id=0) -> None:
        if torch.cuda.is_available() and gpu_id < torch.cuda.device_count():
            self.device = torch.device(f"cuda:{gpu_id}")
        else:
            self.device = torch.device("cpu")
        self.demucs_model = self.init_demucs_model(dm_model_path, dm_config_path)

    def init_demucs_model(self, model_path, config_path):
        model = get_model_from_yaml(config_path, model_path)
        model.to(self.device)
        model.eval()
        return model
    
    def load_audio(self, f):
        a, fs = torchaudio.load(f)
        if (fs != 48000):
            a = torchaudio.functional.resample(a, fs, 48000)
        if a.shape[-1] >= 48000*10:
            a = a[..., :48000*10]
        else:
            a = torch.cat([a, a], -1)
        return a[:, 0:48000*10]
    
    def run(self, audio_path, output_dir='tmp', ext=".flac"):
        os.makedirs(output_dir, exist_ok=True)
        name, _ = os.path.splitext(os.path.basename(audio_path))
        output_paths = []

        for stem in self.demucs_model.sources:
            output_path = os.path.join(output_dir, f"{name}_{stem}{ext}")
            if os.path.exists(output_path):
                output_paths.append(output_path)

        if len(output_paths) == 1:
            vocal_path = output_paths[0]
        else:
            drums_path, bass_path, other_path, vocal_path = self.demucs_model.separate(audio_path, output_dir, device=self.device)
            for path in [drums_path, bass_path, other_path]:
                os.remove(path)
        full_audio = self.load_audio(audio_path)
        vocal_audio = self.load_audio(vocal_path)
        bgm_audio = full_audio - vocal_audio
        return full_audio, vocal_audio, bgm_audio

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ckpt_path", type=str)
    parser.add_argument("input_jsonl", type=str)
    parser.add_argument("save_dir", type=str)
    parser.add_argument("--cfg_coef", type=float, default=1.5)
    parser.add_argument("--temperature", type=float, default=0.9)
    parser.add_argument("--top_k", type=int, default=50)
    parser.add_argument("--top_p", type=float, default=0.0)
    parser.add_argument("--record_tokens", action="store_true")
    parser.add_argument("--record_window", type=int, default=50)
    parser.add_argument("--duration", type=float, default=None)
    args = parser.parse_args()

    print("✅ generate.py parameters:")
    for k, v in vars(args).items():
        print(f"  {k.upper()} = {v}")

    # Load config
    cfg_path = os.path.join(args.ckpt_path, 'config.yaml')
    ckpt_model_path = os.path.join(args.ckpt_path, 'model.pt')
    cfg = OmegaConf.load(cfg_path)
    cfg.mode = 'inference'
    max_duration = cfg.max_dur
    if args.duration is not None:
        max_duration = args.duration

    # Initialize model
    model_light = CodecLM_PL(cfg, ckpt_model_path)
    model_light = model_light.eval().cuda()
    model_light.audiolm.cfg = cfg

    model = CodecLM(
        name="tmp",
        lm=model_light.audiolm,
        audiotokenizer=model_light.audio_tokenizer,
        max_duration=max_duration,
        seperate_tokenizer=model_light.seperate_tokenizer,
    )

    # Load auto prompt
    auto_prompt = torch.load('ckpt/prompt.pt')
    merge_prompt = [item for sublist in auto_prompt.values() for item in sublist]

    # Configure model
    model.set_generation_params(
        duration=max_duration,
        extend_stride=5,
        temperature=args.temperature,
        cfg_coef=args.cfg_coef,
        top_k=args.top_k,
        top_p=args.top_p,
        record_tokens=args.record_tokens,
        record_window=args.record_window
    )

    # Prepare output folders
    #os.makedirs(args.save_dir, exist_ok=True)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    elif not os.path.isdir(save_dir):
        raise RuntimeError(f"Path exists but is not a directory: {save_dir}")

    os.makedirs(os.path.join(args.save_dir, "audios"), exist_ok=True)
    os.makedirs(os.path.join(args.save_dir, "jsonl"), exist_ok=True)

    # Prepare separator
    separator = Separator()

    # Process JSONL
    with open(args.input_jsonl, "r") as fp:
        lines = fp.readlines()

    new_items = []
    for line in lines:
        item = json.loads(line)
        target_wav_name = os.path.join(args.save_dir, "audios", f"{item['idx']}.flac")
        lyric = item["gt_lyric"]
        descriptions = item.get("descriptions", None)

        # Determine prompt
        if "prompt_audio_path" in item:
            assert os.path.exists(item['prompt_audio_path']), f"prompt_audio_path {item['prompt_audio_path']} not found"
            assert 'auto_prompt_audio_type' not in item, f"auto_prompt_audio_type and prompt_audio_path cannot be used together"
            pmt_wav, vocal_wav, bgm_wav = separator.run(item['prompt_audio_path'])
            melody_is_wav = True
        elif "auto_prompt_audio_type" in item:
            assert item["auto_prompt_audio_type"] in auto_prompt_type, f"auto_prompt_audio_type {item['auto_prompt_audio_type']} not found"
            if item["auto_prompt_audio_type"] == "Auto":
                prompt_token = merge_prompt[np.random.randint(0, len(merge_prompt))]
            else:
                prompt_token = auto_prompt[item["auto_prompt_audio_type"]][
                    np.random.randint(0, len(auto_prompt[item["auto_prompt_audio_type"]]))
                ]
            pmt_wav = prompt_token[:, [0], :]
            vocal_wav = prompt_token[:, [1], :]
            bgm_wav = prompt_token[:, [2], :]
            melody_is_wav = False
        else:
            pmt_wav = None
            vocal_wav = None
            bgm_wav = None
            melody_is_wav = True

        generate_inp = {
            'lyrics': [lyric.replace("  ", " ")],
            'descriptions': [descriptions],
            'melody_wavs': pmt_wav,
            'vocal_wavs': vocal_wav,
            'bgm_wavs': bgm_wav,
            'melody_is_wav': melody_is_wav,
        }

        # Generation
        start_time = time.time()
        with torch.autocast(device_type="cuda", dtype=torch.float16):
            tokens = model.generate(**generate_inp, return_tokens=True)
        mid_time = time.time()

        with torch.no_grad():
            if melody_is_wav:
                wav_seperate = model.generate_audio(tokens, pmt_wav, vocal_wav, bgm_wav)
            else:
                wav_seperate = model.generate_audio(tokens)
        end_time = time.time()

        # Save audio
        torchaudio.save(target_wav_name, wav_seperate[0].cpu().float(), cfg.sample_rate)
        print(f"process {item['idx']}, lm cost {mid_time - start_time:.3f}s, diffusion cost {end_time - mid_time:.3f}s")

        item["wav_path"] = target_wav_name
        new_items.append(item)

    # Save new JSONL
    src_jsonl_name = os.path.basename(args.input_jsonl)
    output_jsonl_path = os.path.join(args.save_dir, "jsonl", f"{src_jsonl_name}.jsonl")

    with open(output_jsonl_path, "w", encoding='utf-8') as fw:
        for item in new_items:
            fw.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"✅ All done. Results saved to: {args.save_dir}")

if __name__ == "__main__":
    # Ensure deterministic randomness for reproducibility
    torch.backends.cudnn.enabled = False
    OmegaConf.register_new_resolver("eval", lambda x: eval(x))
    OmegaConf.register_new_resolver("concat", lambda *x: [xxx for xx in x for xxx in xx])
    OmegaConf.register_new_resolver("get_fname", lambda: os.path.splitext(os.path.basename(sys.argv[1]))[0])
    OmegaConf.register_new_resolver("load_yaml", lambda x: list(OmegaConf.load(x)))
    np.random.seed(int(time.time()))
    main()