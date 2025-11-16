import asyncio
import os
import tempfile
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
import torch

if torch.version.cuda == '11.8':
    os.environ["TRITON_PTXAS_PATH"] = "/usr/local/cuda-11.8/bin/ptxas"

os.environ['VLLM_USE_V1'] = '0'
os.environ["CUDA_VISIBLE_DEVICES"] = '0'

from vllm import AsyncLLMEngine, SamplingParams
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.model_executor.models.registry import ModelRegistry
import time
from deepseek_ocr import DeepseekOCRForCausalLM
from PIL import Image
from process.ngram_norepeat import NoRepeatNGramLogitsProcessor
from process.image_process import DeepseekOCRProcessor

ModelRegistry.register_model("DeepseekOCRForCausalLM", DeepseekOCRForCausalLM)

# PDF処理のインポート
try:
    from pdf2image import convert_from_path
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("警告: pdf2imageが見つかりません。PDFファイルは処理できません。")

# FastAPIアプリケーション初期化
app = FastAPI(
    title="DeepSeek OCR API",
    description="画像/PDFファイルからテキストを抽出するOCR API",
    version="1.0.0"
)

# グローバル変数
MODEL_PATH = 'deepseek-ai/DeepSeek-OCR'
SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.pdf')
engine: Optional[AsyncLLMEngine] = None


def load_image_from_file(file_content: bytes, filename: str) -> Optional[Image.Image]:
    """
    アップロードされたファイルから画像を読み込む
    """
    # 対応する拡張子かチェック
    if not filename.lower().endswith(SUPPORTED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"サポートされていないファイル形式: {filename}. 対応形式: {SUPPORTED_EXTENSIONS}"
        )

    try:
        # PDFファイルの処理
        if filename.lower().endswith('.pdf'):
            if not PDF_SUPPORT:
                raise HTTPException(
                    status_code=400,
                    detail="PDFサポートが無効です。pdf2imageをインストールしてください。"
                )

            # 一時ファイルに保存してPDF変換
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(file_content)
                temp_path = temp_file.name

            try:
                images = convert_from_path(
                    temp_path,
                    first_page=1,
                    last_page=1,
                    dpi=300,
                    fmt='RGB'
                )
                if images:
                    img = images[0]
                    return img
                else:
                    raise Exception("PDFファイルの変換結果が空です")
            finally:
                # 一時ファイルを削除
                os.unlink(temp_path)

        # 通常の画像ファイルの処理
        else:
            img = Image.open(io.BytesIO(file_content))

            # RGB形式に変換
            if img.mode != 'RGB':
                img = img.convert('RGB')

            return img

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"画像の読み込みに失敗しました: {str(e)}"
        )


async def stream_generate(image=None, prompt=''):
    """
    OCRモデルでテキストを生成
    """
    global engine

    # エンジンが初期化されていない場合は初期化
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="OCRエンジンが初期化されていません"
        )

    logits_processors = [
        NoRepeatNGramLogitsProcessor(
            ngram_size=30,
            window_size=90,
            whitelist_token_ids={128821, 128822}
        )
    ]

    sampling_params = SamplingParams(
        temperature=0.0,
        max_tokens=8192,
        logits_processors=logits_processors,
        skip_special_tokens=False,
    )

    request_id = f"request-{int(time.time())}"

    if image and '<image>' in prompt:
        request = {
            "prompt": prompt,
            "multi_modal_data": {"image": image}
        }
    elif prompt:
        request = {
            "prompt": prompt
        }
    else:
        raise HTTPException(
            status_code=400,
            detail="プロンプトが指定されていません"
        )

    final_output = ""
    async for request_output in engine.generate(
        request, sampling_params, request_id
    ):
        if request_output.outputs:
            full_text = request_output.outputs[0].text
            final_output = full_text

    return final_output


def extract_deepseek_text(ocr_output: str) -> str:
    """
    OCR出力からテキストを抽出
    """
    lines = ocr_output.splitlines()
    results = []

    for i, line in enumerate(lines):
        line = line.strip()

        if "<|ref|>text<|/ref|>" in line:
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()

                if next_line and not next_line.startswith("<|"):
                    results.append(next_line)

    return "\n".join(results)


@app.on_event("startup")
async def startup_event():
    """
    アプリケーション起動時にOCRエンジンを初期化
    """
    global engine

    print("OCRエンジンを初期化中...")
    engine_args = AsyncEngineArgs(
        model=MODEL_PATH,
        hf_overrides={"architectures": ["DeepseekOCRForCausalLM"]},
        block_size=256,
        max_model_len=8192,
        enforce_eager=False,
        trust_remote_code=True,
        tensor_parallel_size=1,
        gpu_memory_utilization=0.75,
    )
    engine = AsyncLLMEngine.from_engine_args(engine_args)
    print("OCRエンジンの初期化が完了しました")


@app.on_event("shutdown")
async def shutdown_event():
    """
    アプリケーション終了時のクリーンアップ
    """
    global engine
    if engine is not None:
        # エンジンのクリーンアップ処理があればここに追加
        engine = None


@app.get("/")
async def root():
    """
    APIのルートエンドポイント
    """
    return {
        "message": "DeepSeek OCR API",
        "version": "1.0.0",
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
        "engine_initialized": engine is not None,
        "pdf_support": PDF_SUPPORT
    }


@app.post("/ocr")
async def ocr_extract(
    file: UploadFile = File(...),
    crop_mode: bool = Form(default=True),
    prompt: str = Form(default='<image>\n<|grounding|>Convert the document to markdown.')
):
    """
    画像/PDFファイルからテキストを抽出するエンドポイント

    Parameters:
    - file: 画像またはPDFファイル (PNG, JPG, JPEG, WEBP, BMP, TIFF, PDF)
    - crop_mode: クロップモードを有効にするか (デフォルト: True)
    - prompt: OCRプロンプト (デフォルト: '<image>\n<|grounding|>Convert the document to markdown.')

    Returns:
    - extracted_text: 抽出されたテキスト
    - raw_output: モデルの生出力
    - filename: 処理したファイル名
    """
    try:
        # ファイル内容を読み込み
        file_content = await file.read()

        # 画像を読み込み
        image = load_image_from_file(file_content, file.filename)

        # 画像の前処理
        if '<image>' in prompt:
            image_features = DeepseekOCRProcessor().tokenize_with_images(
                images=[image],
                bos=True,
                eos=True,
                cropping=crop_mode
            )
        else:
            image_features = ''

        # OCR実行
        result_out = await stream_generate(image_features, prompt)

        # テキスト抽出
        extracted_text = extract_deepseek_text(result_out)

        return JSONResponse(content={
            "success": True,
            "extracted_text": extracted_text,
            "raw_output": result_out,
            "filename": file.filename
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
