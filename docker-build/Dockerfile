# ---------------------------------------------------
# Stage 1 - Builder
# ---------------------------------------------------
    FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04 AS builder

    # Install Python + build tools + pip
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
    
    # Check pip version
    RUN python3 -m pip --version
    
    # Upgrade pip
    RUN python3 -m pip install --upgrade pip setuptools wheel
    
    # Install torch first
    RUN python3 -m pip install \
        torch==2.6.0 \
        torchvision==0.21.0 \
        torchaudio==2.6.0 \
        --index-url https://download.pytorch.org/whl/cu124
    
    # Create dummy workspace path for pip install
    RUN mkdir -p /workspace/repo/songgeneration
    
    # Copy requirements into builder
    COPY requirements.txt /workspace/repo/songgeneration/
    COPY requirements_nodeps.txt /workspace/repo/songgeneration/
    
    WORKDIR /workspace/repo/songgeneration
    
    RUN python3 -m pip install --no-cache-dir -r requirements.txt
    RUN python3 -m pip install --no-cache-dir -r requirements_nodeps.txt --no-deps
    
    # Install flash-attention wheel
    RUN python3 -m pip install \
        https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.4.post1/flash_attn-2.7.4.post1+cu12torch2.6cxx11abiFALSE-cp310-cp310-linux_x86_64.whl
    
    # Freeze everything
    RUN pip freeze > /workspace/repo/songgeneration/requirements.freeze.txt
    
    # ---------------------------------------------------
    # Stage 2 - Runtime
    # ---------------------------------------------------
    FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04 AS runtime
    
    # Install Python + runtime libraries + git
    RUN apt-get update && \
        apt-get install -y \
            python3.10 \
            python3.10-venv \
            python3.10-dev \
            python3-pip \
            git \
            libsndfile1 \
            ffmpeg \
            libsox-dev && \
        rm -rf /var/lib/apt/lists/*
    
    # Set python3 default to 3.10
    RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
    
    # Upgrade pip
    RUN python3 -m pip install --upgrade pip setuptools wheel
    
    # Copy Python dist-packages from builder
    COPY --from=builder /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
    
    # Copy entrypoint script into container
    COPY app_files/docker_entrypoint.sh /docker_entrypoint.sh
    RUN chmod +x /docker_entrypoint.sh
    
    # Default working directory
    WORKDIR /workspace
    
    # Default command
    CMD ["/docker_entrypoint.sh"]