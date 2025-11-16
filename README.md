# DeepSeek OCR - Docker環境

このプロジェクトでは、GPU版とCPU版の2つのDocker環境を提供しています。

## 📁 ファイル構成
```
deepseekOCR/
├── Dockerfile              # GPU版
├── Dockerfile.cpu          # CPU版
├── docker-compose.yml      # GPU版の設定
├── docker-compose.cpu.yml  # CPU版の設定
└── README.md              # このファイル
```

## 🚀 使い方

### GPU版（NVIDIA GPU必須）

#### ビルド
```powershell
docker-compose build
```

#### 起動
```powershell
docker-compose up -d
```

---

### CPU版（GPUなしで動作）

#### ビルド
```powershell
docker-compose -f docker-compose.cpu.yml build
```

#### 起動
```powershell
docker-compose -f docker-compose.cpu.yml up -d
```

---

## 🔧 コンテナ操作

### コンテナに入る

**GPU版:**
```powershell
docker-compose exec deepseek-ocr bash
```

**CPU版:**
```powershell
docker-compose -f docker-compose.cpu.yml exec deepseek-ocr-cpu bash
```

### ログを見る

**GPU版:**
```powershell
docker-compose logs -f
```

**CPU版:**
```powershell
docker-compose -f docker-compose.cpu.yml logs -f
```

### コンテナを停止

**GPU版:**
```powershell
docker-compose down
```

**CPU版:**
```powershell
docker-compose -f docker-compose.cpu.yml down
```

### 両方停止
```powershell
docker-compose down
docker-compose -f docker-compose.cpu.yml down
```

---

## ⚙️ 両方同時に起動

GPU版とCPU版を同時に起動することも可能です：
```powershell
# GPU版を起動
docker-compose up -d

# CPU版を起動
docker-compose -f docker-compose.cpu.yml up -d
```

---

## 📊 比較表

| 項目 | GPU版 | CPU版 |
|------|-------|-------|
| **必要なハードウェア** | NVIDIA GPU | CPUのみ |
| **処理速度** | 高速 | 低速 |
| **コンテナ名** | deepseek-ocr | deepseek-ocr-cpu |
| **Dockerfile** | Dockerfile | Dockerfile.cpu |
| **docker-compose** | docker-compose.yml | docker-compose.cpu.yml |
| **使用ライブラリ** | vLLM | transformers |

---

## ⚠️ 注意事項

### GPU版
- NVIDIA GPUとDocker Desktop with GPU supportが必要
- CUDA 11.8対応
- vLLMを使用

### CPU版
- GPUは不要
- 処理速度はGPU版の1/100以上遅くなる可能性
- transformersライブラリを使用（vLLMの代替）
- テスト・開発用途に最適

---

## 🛠️ トラブルシューティング

### ビルドが失敗する場合

タイムアウトエラーが発生する場合は、再度ビルドを試してください：
```powershell
docker-compose build --no-cache
```

または
```powershell
docker-compose -f docker-compose.cpu.yml build --no-cache
```

### コンテナが起動しない場合

Docker Desktopが起動しているか確認してください。

---

## 📝 開発環境

### 仮想環境の作成（ローカル開発用）
```powershell
# 仮想環境の作成
uv venv deepseek-ocr --python 3.12.9

# 仮想環境の有効化
deepseek-ocr\Scripts\activate

# パッケージのインストール
uv pip install -r requirements.txt
```

---

## 📚 参考リンク

- [DeepSeek-OCR GitHub](https://github.com/deepseek-ai/DeepSeek-OCR)
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-docker)