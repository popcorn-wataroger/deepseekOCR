# DeepSeek OCR API (Docker版)

Docker上でDeepSeek OCR APIを起動して、画像/PDFファイルからテキストを抽出します。

## ✅ 動作確認済み

- ✅ Docker環境でのOCR APIサーバー起動
- ✅ 画像ファイル（JPG, PNG, TIFF等）からのOCR
- ✅ PDFファイルからのOCR（1ページ目、300 DPI）
- ✅ 日本語テキストの正確な抽出
- ✅ レシート、領収書、文書などの読み取り

## ファイル構成

```
docker_api_test/
├── Dockerfile                  # Dockerイメージ定義
├── docker-compose.yml          # Docker Compose設定
├── api_router.py               # FastAPI ルーター
├── image_loader.py             # 画像読み込みモジュール
├── deepseek_ocr_engine.py      # DeepSeek OCRエンジン
├── testdata/                   # テストデータ用ディレクトリ
│   └── inputs/                 # 入力画像ファイル
├── test_api.py                 # Pythonテストスクリプト
├── test_api.sh                 # curlテストスクリプト
└── README.md                   # このファイル
```

## 必要な環境

- Docker & Docker Compose
- NVIDIA GPU (CUDA 11.8対応)
- nvidia-docker2
- 十分なディスクスペース（モデルダウンロード用に約10GB）

## セットアップ & 起動

### 1. Dockerイメージのビルドとコンテナ起動

```bash
cd docker_api_test

# イメージのビルドとコンテナ起動（初回は時間がかかります）
docker-compose up --build
```

初回起動時は以下の処理が行われます：
- Dockerイメージのビルド（20-30分程度）
- DeepSeek-OCRモデルのダウンロード（約60秒、数GB）
- OCRエンジンの初期化（約20秒）

起動成功のログ例：
```
deepseek-ocr-api_1  | OCRエンジンの初期化が完了しました
deepseek-ocr-api_1  | INFO:     Application startup complete.
deepseek-ocr-api_1  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 2. バックグラウンドで起動

```bash
docker-compose up -d
```

### 3. ログの確認

```bash
# リアルタイムでログを確認
docker-compose logs -f

# 特定のサービスのログのみ
docker-compose logs -f deepseek-ocr-api
```

### 4. 停止

```bash
docker-compose down
```

## APIの使い方

APIは `http://localhost:8000` で利用可能です。

### ヘルスチェック

```bash
curl http://localhost:8000/health
```

**レスポンス例:**
```json
{
  "status": "healthy",
  "engine_initialized": true,
  "supported_formats": [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".pdf"]
}
```

### ルート情報

```bash
curl http://localhost:8000/
```

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

### OCR実行

#### 基本的な使い方

```bash
# 進捗表示なし（-s オプション）
curl -s -X POST "http://localhost:8000/ocr" \
  -F "file=@/path/to/image.jpg" \
  -F "crop_mode=true" | python3 -c "import sys, json; print(json.load(sys.stdin)['extracted_text'])"
```

#### 完全なレスポンスを見る

```bash
curl -s -X POST "http://localhost:8000/ocr" \
  -F "file=@/path/to/image.jpg" \
  -F "crop_mode=true" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), ensure_ascii=False, indent=2))"
```

#### PDFファイル

```bash
curl -s -X POST "http://localhost:8000/ocr" \
  -F "file=@/path/to/document.pdf" \
  -F "crop_mode=true" | python3 -c "import sys, json; print(json.load(sys.stdin)['extracted_text'])"
```

#### カスタムプロンプト

```bash
curl -s -X POST "http://localhost:8000/ocr" \
  -F "file=@/path/to/image.jpg" \
  -F "crop_mode=true" \
  -F "prompt=<image>\n<|grounding|>Convert the document to markdown." \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['extracted_text'])"
```

### 実行例（KFCレシート）

```bash
curl -s -X POST "http://localhost:8000/ocr" \
  -F "file=@testdata/inputs/IMG_5540.jpg" \
  -F "crop_mode=true" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['extracted_text'])"
```

**出力例:**
```
KFC  
今夏は正  

様  

近江八幡店  
0748-31-2080  
近江八幡市鷹飼町529  

商品の不足、その他ご意見など
ございましたら  
下記フリーダイヤルまで。  
0120-208-048  

*は軽減税率対象  

1*CP203(ﾎﾞﾃﾄS) ¥270  
1*クリスピー1ピース半額 ¥140  
1*にんにく醤油チキン ¥330  

お買上 ¥740  
合計 ¥740  
(内消費税 ¥54)  
8%対象 ¥740(税 ¥54)  
10%対象 ¥0(税 ¥0)  
クレジット ¥740  

上記正に領収いたしました。
```

### Pythonクライアント例

```python
import requests

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

## APIエンドポイント

### `GET /`
API情報とエンドポイント一覧を返す

### `GET /health`
APIのヘルスチェック

### `POST /ocr`
画像/PDFファイルからテキストを抽出

**パラメータ:**
- `file` (required): 画像またはPDFファイル
- `crop_mode` (optional, default: true): クロップモードを有効にするか
- `prompt` (optional, default: `<image>\n<Free OCR.`): OCRプロンプト

**レスポンス:**
```json
{
  "success": true,
  "extracted_text": "抽出されたテキスト...",
  "raw_output": "モデルの生出力...",
  "filename": "sample.jpg",
  "crop_mode": true
}
```

## 対応ファイル形式

- 画像: PNG, JPG, JPEG, WEBP, BMP, TIFF
- PDF: PDF（1ページ目のみ、300 DPI変換）

## システム構成

### モジュール構成

1. **api_router.py** - FastAPI ルーター
   - エンドポイント定義（`/`, `/health`, `/ocr`）
   - リクエスト/レスポンス処理
   - エンジンの初期化とシャットダウン管理

2. **image_loader.py** - 画像読み込みモジュール
   - PNG, JPG, JPEG, WEBP, BMP, TIFF対応
   - PDF対応（pdf2image使用、1ページ目を300 DPIで変換）
   - RGB形式への統一変換
   - エラーハンドリング

3. **deepseek_ocr_engine.py** - DeepSeekOCRエンジン
   - `DeepSeekOCREngine`クラスでエンジンを管理
   - 画像の前処理（クロップモード対応）
   - OCR推論実行
   - テキスト抽出処理

### リソース使用状況

- **GPUメモリ**: 約6.23 GiB（モデル）+ 28.34 GiB（KVキャッシュ）= 約35 GiB
- **GPU使用率**: 75%（設定値）
- **最大同時実行**: 約60リクエスト（8192トークン/リクエストの場合）

## トラブルシューティング

### ポート8000が使用中の場合

`docker-compose.yml`のポートマッピングを変更:
```yaml
ports:
  - "8080:8000"  # 8080など別のポートに変更
```

### GPU関連のエラー

```bash
# nvidia-dockerのインストール確認
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### メモリ不足エラー

`deepseek_ocr_engine.py`の`gpu_memory_utilization`を調整:
```python
gpu_memory_utilization=0.5,  # 0.75から0.5に変更
```

### コンテナの再起動

```bash
# コンテナを停止して削除
docker-compose down

# ボリュームも含めて完全削除（モデルも再ダウンロード）
docker-compose down -v

# 再起動
docker-compose up --build
```

### ログレベルの変更

`api_router.py`の最後の部分で`log_level`を変更:
```python
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,
    log_level="debug"  # infoからdebugに変更
)
```

## 開発中のファイル更新

ホスト側でファイルを編集すると、コンテナ内に自動的に反映されます（ボリュームマウント）。

```bash
# 変更を反映するためにコンテナを再起動
docker-compose restart
```

## パフォーマンス

- **初回リクエスト**: 数秒〜数十秒（モデルのウォームアップ）
- **2回目以降**: 1〜3秒程度
- **GPU使用率**: 75%程度
- **同時実行**: 最大60リクエスト（8192トークン/リクエストの場合）

## セキュリティ注意事項

⚠️ **このAPIは開発/テスト用です**

本番環境で使用する場合は、以下の対策を実装してください：
- 適切な認証・認可（API キー、OAuth等）
- ファイルサイズ制限の設定
- レート制限の実装
- HTTPS/TLSの使用
- ファイルタイプの厳密な検証
- ログ監視とアラート設定

## ライセンス

このプロジェクトは、DeepSeek-OCRのライセンスに従います。
- DeepSeek-OCR: https://github.com/deepseek-ai/DeepSeek-OCR

## 参考リンク

- [DeepSeek-OCR GitHub](https://github.com/deepseek-ai/DeepSeek-OCR)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [vLLM Documentation](https://docs.vllm.ai/)

