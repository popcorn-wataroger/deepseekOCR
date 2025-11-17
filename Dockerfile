FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04

# 必要なパッケージのインストール
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    git \
    wget \
    python3-pip \
    python3-setuptools \
    python3-dev \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# DeepSeek-OCRリポジトリのクローン
RUN git clone https://github.com/deepseek-ai/DeepSeek-OCR.git /DeepSeek-OCR

# PyTorchとvLLMのインストール
RUN pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu118
RUN wget https://github.com/vllm-project/vllm/releases/download/v0.8.5/vllm-0.8.5+cu118-cp38-abi3-manylinux1_x86_64.whl
RUN pip install vllm-0.8.5+cu118-cp38-abi3-manylinux1_x86_64.whl

# DeepSeek-OCRの依存関係をインストール
WORKDIR /DeepSeek-OCR
RUN pip install -r requirements.txt
RUN pip install flash-attn==2.7.3 --no-build-isolation

# FastAPI関連パッケージとPDF処理用パッケージをインストール
RUN pip install fastapi uvicorn[standard] pdf2image pillow python-multipart

# ポート8000を公開
EXPOSE 8000
