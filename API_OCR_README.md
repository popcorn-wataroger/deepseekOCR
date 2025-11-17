# DeepSeek OCR API

DeepSeekOCRを使用した画像/PDFからのテキスト抽出API

## ファイル構成

```
docker_test/
├── api_router.py              # FastAPI ルーター（メインファイル）
├── image_loader.py            # 画像読み込みモジュール
├── deepseek_ocr_engine.py     # DeepSeek OCRエンジンモジュール
```

## 機能

### 3つのモジュール

1. **api_router.py** - APIルーター
   - FastAPIアプリケーションの定義
   - エンドポイント `/ocr`, `/health`, `/` の実装
   - リクエスト/レスポンス処理

2. **image_loader.py** - 画像の読み込み
   - 画像ファイル（PNG, JPG, JPEG, WEBP, BMP, TIFF）の読み込み
   - PDFファイルの読み込み（1ページ目のみ、300 DPI）
   - RGB形式への統一変換

3. **deepseek_ocr_engine.py** - DeepSeekOCR
   - OCRエンジンの初期化と管理
   - 画像の前処理（クロップモード対応）
   - OCR推論実行
   - テキスト抽出処理

## 対応ファイル形式

- 画像: PNG, JPG, JPEG, WEBP, BMP, TIFF
- PDF: PDF（1ページ目のみ、pdf2imageが必要）

## APIエンドポイント

### 1. ルート - `GET /`

API情報とエンドポイント一覧を返す

**レスポンス例:**
```json
{
  "message": "DeepSeek OCR API",
  "version": "1.0.0",
  "supported_formats": [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".pdf"],
  "endpoints": {
    "/ocr": "POST - 画像/PDFファイルからテキストを抽出",
    "/health": "GET - ヘルスチェック"
  }
}
```

### 2. ヘルスチェック - `GET /health`

APIの状態を確認

**レスポンス例:**
```json
{
  "status": "healthy",
  "engine_initialized": true,
  "pdf_support": true,
  "supported_formats": [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".pdf"]
}
```

### 3. OCR抽出 - `POST /ocr`

画像/PDFファイルからテキストを抽出

**パラメータ:**
- `file` (required): 画像またはPDFファイル
- `crop_mode` (optional, default: `true`): クロップモードを有効にするか
- `prompt` (optional, default: `<image>\n<Free OCR.`): OCRプロンプト

**レスポンス例:**
```json
{
  "success": true,
  "extracted_text": "抽出されたテキスト...",
  "raw_output": "モデルの生出力...",
  "filename": "example.jpg",
  "crop_mode": true
}
```

## 使い方

### 1. サーバー起動

```bash
python api_router.py
```

サーバーは `http://localhost:8000` で起動します。

### 2. curlでのテスト

```bash
# 画像ファイルのOCR
curl -X POST "http://localhost:8000/ocr" \
  -F "file=@/path/to/image.jpg" \
  -F "crop_mode=true"

# PDFファイルのOCR
curl -X POST "http://localhost:8000/ocr" \
  -F "file=@/path/to/document.pdf" \
  -F "crop_mode=true"

# カスタムプロンプトを使用
curl -X POST "http://localhost:8000/ocr" \
  -F "file=@/path/to/image.jpg" \
  -F "crop_mode=true" \
  -F "prompt=<image>\n<|grounding|>Convert the document to markdown."
```

### 3. Pythonクライアント例

```python
import requests

# OCR実行
def ocr_file(file_path, crop_mode=True):
    url = "http://localhost:8000/ocr"
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {'crop_mode': crop_mode}
        
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print("抽出されたテキスト:")
            print(result['extracted_text'])
            return result
        else:
            print(f"エラー: {response.status_code}")
            print(response.json())
            return None

# 使用例
result = ocr_file('/path/to/image.jpg')
```

## 環境変数

以下の環境変数が設定されます:

- `VLLM_USE_V1`: `0` (vLLM v1を無効化)
- `CUDA_VISIBLE_DEVICES`: `0` (GPU 0を使用)
- `TRITON_PTXAS_PATH`: CUDA 11.8使用時に設定

## 要件

`requirements_api.txt` に記載の依存パッケージが必要です:

```txt
fastapi
uvicorn
torch
vllm
pillow
pdf2image  # PDF対応に必要
```

## 参考実装

`deepseek_ocr_custom.py` はスタンドアロン版の参考実装です。このファイルの実装を踏襲して、APIサーバーを構築しています。

## 注意事項

- PDF処理には `pdf2image` と `poppler` が必要です
- GPU環境が必要です（CUDA対応）
- モデルは初回起動時に自動ダウンロードされます
- モデルパス: `deepseek-ai/DeepSeek-OCR`

## Docker環境での実行

Docker環境で実行する場合は、`docker-compose.yml` と `Dockerfile` を使用してください。

```bash
docker-compose up
```
