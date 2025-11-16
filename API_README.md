# DeepSeek OCR API

DeepSeek OCRモデルを使用した画像/PDFファイルからのテキスト抽出API

## 機能

- 画像ファイル(PNG, JPG, JPEG, WEBP, BMP, TIFF)からのテキスト抽出
- PDFファイル(最初のページ)からのテキスト抽出
- FastAPIベースのRESTful API
- 非同期処理対応

## セットアップ

### 1. 必要なライブラリのインストール

```bash
# FastAPI関連のライブラリをインストール
pip install -r requirements_api.txt

# 既存のOCR関連ライブラリは別途インストール済みであることを前提
```

### 2. サーバーの起動

```bash
# 方法1: Pythonで直接起動
python api_server.py

# 方法2: uvicornで起動（推奨）
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

サーバーが起動すると、以下のURLでアクセスできます：
- API: http://localhost:8000
- ドキュメント: http://localhost:8000/docs
- 別形式ドキュメント: http://localhost:8000/redoc

## APIエンドポイント

### 1. ルート (`GET /`)

APIの基本情報を取得

```bash
curl http://localhost:8000/
```

### 2. ヘルスチェック (`GET /health`)

サーバーの状態を確認

```bash
curl http://localhost:8000/health
```

### 3. OCR実行 (`POST /ocr`)

画像/PDFファイルからテキストを抽出

#### パラメータ

- `file` (必須): 画像またはPDFファイル
- `crop_mode` (オプション): クロップモードを有効にするか (デフォルト: `true`)
- `prompt` (オプション): OCRプロンプト (デフォルト: `<image>\n<|grounding|>Convert the document to markdown.`)

#### curlでの使用例

```bash
# 画像ファイルをアップロード
curl -X POST "http://localhost:8000/ocr" \
  -F "file=@/path/to/your/image.jpg"

# crop_modeを指定
curl -X POST "http://localhost:8000/ocr" \
  -F "file=@/path/to/your/image.jpg" \
  -F "crop_mode=false"

# カスタムプロンプトを指定
curl -X POST "http://localhost:8000/ocr" \
  -F "file=@/path/to/your/document.pdf" \
  -F "prompt=<image>\n<|grounding|>Extract all text from this document."
```

#### Pythonでの使用例

```python
import requests

# 画像ファイルをアップロード
url = "http://localhost:8000/ocr"
files = {"file": open("image.jpg", "rb")}
response = requests.post(url, files=files)

result = response.json()
print("抽出されたテキスト:")
print(result["extracted_text"])
```

#### レスポンス例

```json
{
  "success": true,
  "extracted_text": "抽出されたテキストがここに表示されます",
  "raw_output": "モデルの生出力（マークダウン形式）",
  "filename": "uploaded_file.jpg"
}
```

## Dockerでの実行（オプション）

Dockerfileを作成してコンテナ化することもできます：

```dockerfile
FROM python:3.10

WORKDIR /app

# 必要なライブラリをインストール
COPY requirements_api.txt .
RUN pip install -r requirements_api.txt

# アプリケーションファイルをコピー
COPY api_server.py .
COPY deepseek_ocr.py .
COPY process/ ./process/

# ポート8000を公開
EXPOSE 8000

# サーバー起動
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

## トラブルシューティング

### PDF処理ができない

PDFサポートには`pdf2image`とシステムの`poppler`が必要です：

```bash
# Python パッケージをインストール
pip install pdf2image

# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils

# Windows
# https://github.com/oschwartz10612/poppler-windows/releases/ からダウンロード
```

### GPUメモリ不足

`api_server.py`の`gpu_memory_utilization`パラメータを調整してください：

```python
# 75%から50%に変更
gpu_memory_utilization=0.50,
```

### ポート8000が使用中

別のポートで起動してください：

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8080
```

## ファイル構成

```
.
├── api_server.py           # FastAPI サーバー
├── deepseek_ocr_custom.py  # 既存のOCRスクリプト
├── requirements_api.txt    # API用の追加ライブラリ
└── API_README.md          # このファイル
```

## 注意事項

- サーバー起動時にOCRモデルがロードされるため、起動に時間がかかります
- GPU環境が必要です（CUDA対応）
- 大きなファイルのアップロードには時間がかかる場合があります
