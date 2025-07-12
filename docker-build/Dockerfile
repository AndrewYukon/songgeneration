# ---------------------------------------------------
# Base image: NVIDIA CUDA 12.4.1, Ubuntu 22.04
# ---------------------------------------------------
    FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

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
    RUN mkdir -p /repo
    
    # ---------------------------------------------------
    # Clone your repo
    # ---------------------------------------------------
    RUN git clone https://github.com/AndrewYukon/songgeneration /repo/songgeneration
    
    # ---------------------------------------------------
    # Set workdir
    # ---------------------------------------------------
    WORKDIR /repo/songgeneration
    
    # ---------------------------------------------------
    # Install your Python dependencies
    # ---------------------------------------------------
    RUN python3 -m pip install --no-cache-dir -r requirements.txt
    RUN python3 -m pip install --no-cache-dir -r requirements_nodeps.txt --no-deps
    

    # ---------------------------------------------------
    # Install flash-attention wheel
    # ---------------------------------------------------
    RUN python3 -m pip install \
        https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.4.post1/flash_attn-2.7.4.post1+cu12torch2.6cxx11abiFALSE-cp310-cp310-linux_x86_64.whl
    
    # ---------------------------------------------------
    # Copy docker entrypoint script
    # ---------------------------------------------------
    RUN mkdir -p /repo/songgeneration/app
    COPY app_files/ /repo/songgeneration/app/
    
    RUN chmod +x /repo/songgeneration/app/docker_entrypoint.sh
    
    # ---------------------------------------------------
    # Default shell
    # CMD ["/repo/songgeneration/app/docker_entrypoint.sh"]
    # ---------------------------------------------------
    
    CMD ["/repo/songgeneration/app/docker_entrypoint.sh"]