# ---------------------------------------------------
# Base image: NVIDIA CUDA 12.4.1, Ubuntu 22.04
# ---------------------------------------------------
    FROM nvidia/cuda:12.4.1-cudnn8-devel-ubuntu22.04

    # ---------------------------------------------------
    # Install Python 3.10 + dev tools
    # ---------------------------------------------------
    RUN apt-get update && \
        apt-get install -y \
            python3.10 \
            python3.10-venv \
            python3.10-dev \
            python3-pip \
            git \
            wget \
            curl \
            build-essential \
            libsndfile1 \
            ffmpeg \
            libsox-dev && \
        rm -rf /var/lib/apt/lists/*
    
    # Set python3 default to 3.10
    RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
    
    # ---------------------------------------------------
    # Upgrade pip
    # ---------------------------------------------------
    RUN python3 -m pip install --upgrade pip setuptools wheel
    
    # ---------------------------------------------------
    # Install PyTorch 2.6.0 with CUDA 12.4
    # ---------------------------------------------------
    RUN python3 -m pip install \
        torch==2.6.0 \
        torchvision==0.21.0 \
        torchaudio==2.6.0 \
        --index-url https://download.pytorch.org/whl/cu124
    
    # ---------------------------------------------------
    # Create workspace dirs
    # ---------------------------------------------------
    RUN mkdir -p /workspace/repo
    RUN mkdir -p /workspace/SongGeneration/jsonl
    RUN mkdir -p /workspace/SongGeneration/output
    
    # ---------------------------------------------------
    # Clone your repo
    # ---------------------------------------------------
    RUN git clone https://github.com/AndrewYukon/songgeneration /workspace/repo/songgeneration
    
    # ---------------------------------------------------
    # Set workdir
    # ---------------------------------------------------
    WORKDIR /workspace/repo/songgeneration
    
    # ---------------------------------------------------
    # Install your Python dependencies
    # ---------------------------------------------------
    
    # Install requirements.txt
    RUN python3 -m pip install --no-cache-dir -r requirements.txt
    
    # Install requirements_nodeps.txt without deps
    RUN python3 -m pip install --no-cache-dir -r requirements_nodeps.txt --no-deps
    
    # ---------------------------------------------------
    # Install flash-attention wheel
    # ---------------------------------------------------
    RUN python3 -m pip install \
        https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.4.post1/flash_attn-2.7.4.post1+cu12torch2.6cxx11abiFALSE-cp310-cp310-linux_x86_64.whl
    
    # ---------------------------------------------------
    # Link ckpt and third_party into repo root
    # ---------------------------------------------------
    RUN ln -s /workspace/SongGeneration/ckpt /workspace/repo/songgeneration/ckpt && \
        ln -s /workspace/SongGeneration/third_party /workspace/repo/songgeneration/third_party
    
    # ---------------------------------------------------
    # Default shell
    # ---------------------------------------------------
    CMD ["/bin/bash"]