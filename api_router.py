"""
FastAPI ルーターモジュール
OCR APIのエンドポイントを定義
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

from image_loader import load_image_from_file, SUPPORTED_EXTENSIONS
from deepseek_ocr_engine import ocr_engine


# FastAPIアプリケーション初期化
app = FastAPI(
    title="DeepSeek OCR API",
    description="画像/PDFファイルからテキストを抽出するOCR API",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """
    アプリケーション起動時にOCRエンジンを初期化
    """
    await ocr_engine.initialize()


@app.on_event("shutdown")
async def shutdown_event():
    """
    アプリケーション終了時のクリーンアップ
    """
    ocr_engine.shutdown()


@app.get("/")
async def root():
    """
    APIのルートエンドポイント
    """
    return {
        "message": "DeepSeek OCR API",
        "version": "1.0.0",
        "supported_formats": SUPPORTED_EXTENSIONS,
        "endpoints": {
            "/ocr": "POST - 画像/PDFファイルからテキストを抽出",
            "/health": "GET - ヘルスチェック"
        }
    }


@app.get("/health")
async def health_check():
    """
    ヘルスチェックエンドポイント
    """
    return {
        "status": "healthy",
        "engine_initialized": ocr_engine.is_initialized(),
        "supported_formats": SUPPORTED_EXTENSIONS
    }


@app.post("/ocr")
async def ocr_extract(
    file: UploadFile = File(..., description="画像またはPDFファイル"),
    crop_mode: bool = Form(default=True, description="クロップモードを有効にするか"),
    prompt: str = Form(
        default='<image>\n<Free OCR.',
        description="OCRプロンプト"
    )
):
    """
    画像/PDFファイルからテキストを抽出するエンドポイント

    Parameters:
    - file: 画像またはPDFファイル (PNG, JPG, JPEG, WEBP, BMP, TIFF, PDF)
    - crop_mode: クロップモードを有効にするか (デフォルト: True)
    - prompt: OCRプロンプト (デフォルト: '<image>\n<Free OCR.')

    Returns:
    - success: 成功フラグ
    - extracted_text: 抽出されたテキスト
    - raw_output: モデルの生出力
    - filename: 処理したファイル名
    - crop_mode: 使用したクロップモード
    """
    try:
        # エンジンの初期化チェック
        if not ocr_engine.is_initialized():
            raise HTTPException(
                status_code=503,
                detail="OCRエンジンが初期化されていません。しばらく待ってから再度お試しください。"
            )

        # ファイル内容を読み込み
        file_content = await file.read()

        # 画像を読み込み（RGB形式）
        image = load_image_from_file(file_content, file.filename)

        # 画像の前処理
        if '<image>' in prompt:
            image_features = ocr_engine.preprocess_image(
                image=image,
                crop_mode=crop_mode
            )
        else:
            image_features = None

        # OCR推論実行
        raw_output = await ocr_engine.generate(
            image_features=image_features,
            prompt=prompt
        )

        # テキスト抽出
        extracted_text = ocr_engine.extract_text(raw_output)

        return JSONResponse(content={
            "success": True,
            "extracted_text": extracted_text,
            "raw_output": raw_output,
            "filename": file.filename,
            "crop_mode": crop_mode
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OCR処理中にエラーが発生しました: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    # サーバー起動
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
