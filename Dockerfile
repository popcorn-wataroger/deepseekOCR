FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    git \
    wget \
    python3-pip \
    python3-setuptools \
    python3-dev \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN git clone https://github.com/deepseek-ai/DeepSeek-OCR.git /DeepSeek-OCR
WORKDIR /DeepSeek-OCR
RUN pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu118
RUN wget https://github.com/vllm-project/vllm/releases/download/v0.8.5/vllm-0.8.5+cu118-cp38-abi3-manylinux1_x86_64.whl
RUN pip install --timeout=600 --retries=10 vllm-0.8.5+cu118-cp38-abi3-manylinux1_x86_64.whl
# RUN pip install vllm-0.8.5+cu118-cp38-abi3-manylinux1_x86_64.whl
RUN pip install -r requirements.txt
RUN pip install flash-attn==2.7.3 --no-build-isolation
RUN pip install pdf2image pillow


# ############### Stage 1 : DeepSeek-OCR を取得 ###############
# FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04 AS builder

# RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
#     git \
#     python3-pip \
#     python3-setuptools \
#     python3-dev \
#     && apt-get clean && rm -rf /var/lib/apt/lists/*

# # DeepSeek-OCR を clone（builder 内）
# RUN git clone https://github.com/deepseek-ai/DeepSeek-OCR.git /DeepSeek-OCR


# ############### Stage 2 : 本番環境 ###############
# FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04

# RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
#     git \
#     wget \
#     python3-pip \
#     python3-setuptools \
#     python3-dev \
#     poppler-utils \
#     && apt-get clean && rm -rf /var/lib/apt/lists/*

# # -------- DeepSeek-OCR の dependencies --------
# COPY --from=builder /DeepSeek-OCR /DeepSeek-OCR
# WORKDIR /DeepSeek-OCR

# RUN pip install -r requirements.txt

# # PyTorch cu118
# RUN pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 \
#     --index-url https://download.pytorch.org/whl/cu118

# # vLLM (cu118)
# RUN wget https://github.com/vllm-project/vllm/releases/download/v0.8.5/vllm-0.8.5+cu118-cp38-abi3-manylinux1_x86_64.whl \
#     && pip install vllm-0.8.5+cu118-cp38-abi3-manylinux1_x86_64.whl

# RUN pip install flash-attn==2.7.3 --no-build-isolation

# # PDF & OCR utilities + FastAPI
# RUN pip install pdf2image pillow pillow-heif fastapi uvicorn python-multipart


# ############### FastAPI アプリ配置 ###############
# WORKDIR /app

# # FastAPI アプリケーション本体
# COPY ./api_server.py /app/api_server.py

# # DeepSeek-OCR の process モジュールを builder からコピー
# COPY --from=builder /DeepSeek-OCR/DeepSeek-OCR-master/DeepSeek-OCR-vllm/process /app/process

# ############### FastAPI 起動 ###############
# CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]