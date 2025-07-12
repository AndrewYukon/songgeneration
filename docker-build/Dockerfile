# ---------------------------------------------------
# Stage 1 - Builder
# ---------------------------------------------------
    FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04 AS builder

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
    
    RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
    
    RUN python3 -m pip install --upgrade pip setuptools wheel
    
    RUN python3 -m pip install \
        torch==2.6.0 \
        torchvision==0.21.0 \
        torchaudio==2.6.0 \
        --index-url https://download.pytorch.org/whl/cu124
    
    # Create dummy workspace path for pip install
    RUN mkdir -p /workspace/repo/songgeneration
    
    # Copy only requirements into builder stage
    COPY requirements.txt /workspace/repo/songgeneration/
    COPY requirements_nodeps.txt /workspace/repo/songgeneration/
    
    WORKDIR /workspace/repo/songgeneration
    
    RUN python3 -m pip install --no-cache-dir -r requirements.txt
    RUN python3 -m pip install --no-cache-dir -r requirements_nodeps.txt --no-deps
    
    RUN python3 -m pip install \
        https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.4.post1/flash_attn-2.7.4.post1+cu12torch2.6cxx11abiFALSE-cp310-cp310-linux_x86_64.whl
    
    # Freeze everything
    RUN pip freeze > /workspace/repo/songgeneration/requirements.freeze.txt
    
    # ---------------------------------------------------
    # Stage 2 - Runtime
    # ---------------------------------------------------
    FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04 AS runtime
    
    RUN apt-get update && \
        apt-get install -y \
            python3.10 \
            python3.10-venv \
            libsndfile1 \
            ffmpeg \
            libsox-dev && \
        rm -rf /var/lib/apt/lists/*
    
    RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
    
    RUN python3 -m pip install --upgrade pip setuptools wheel
    
    # Copy Python site-packages from builder
    COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
    
    # Copy only the entrypoint script
    COPY app_files/docker_entrypoint.sh /docker_entrypoint.sh
    RUN chmod +x /docker_entrypoint.sh
    
    # Default workdir is workspace
    WORKDIR /workspace
    
    CMD ["/docker_entrypoint.sh"]