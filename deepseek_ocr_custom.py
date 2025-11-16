import asyncio
import re
import os

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
from PIL import Image, ImageDraw, ImageFont, ImageOps
import numpy as np
from tqdm import tqdm
from process.ngram_norepeat import NoRepeatNGramLogitsProcessor
from process.image_process import DeepseekOCRProcessor

ModelRegistry.register_model("DeepseekOCRForCausalLM", DeepseekOCRForCausalLM)

# PDF処理のインポート（オプション）
try:
    from pdf2image import convert_from_path
    PDF_SUPPORT = True
    print("PDF処理サポートが有効です。")
except ImportError:
    PDF_SUPPORT = False
    print("警告: pdf2imageが見つかりません。PDFファイルは処理できません。")
MODEL_PATH = 'deepseek-ai/DeepSeek-OCR' # change to your model path
# INPUT_PATH = '/testdata/inputs/test.tiff'
INPUT_PATH = '/testdata/inputs/IMG_8296.jpg'
OUTPUT_PATH = '/testdata/outputs/'
CROP_MODE = True
PROMPT = '<image>\n<|grounding|>Convert the document to markdown.'
SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.pdf') # 対応する画像ファイルの拡張子（大文字小文字両対応）

def load_image(image_path):
    
    # ファイルの存在確認を追加
    if not os.path.exists(image_path):
        print(f"エラー: ファイルが見つかりません: {image_path}")
        return None
    
    filename = os.path.basename(image_path)
    
    # 対応する拡張子かチェック
    if not filename.lower().endswith(SUPPORTED_EXTENSIONS):
        print(f"エラー: サポートされていないファイル形式: {filename}")
        return None
    
    try:
        # PDFファイルの処理
        if filename.lower().endswith('.pdf'):
            if PDF_SUPPORT:
                print(f"PDFファイルを画像に変換中: {filename}")
                try:
                    # PDFの最初のページを画像として変換（300 DPIで高品質変換）
                    images = convert_from_path(
                        image_path, 
                        first_page=1, 
                        last_page=1,
                        dpi=300,  # 高品質変換
                        fmt='RGB'  # RGB形式で出力
                    )
                    if images:
                        img = images[0]  # 最初のページを使用
                        print(f"  PDF変換完了: サイズ={img.size}, モード={img.mode}, DPI=300")
                        return img
                    else:
                        raise Exception("PDFファイルの変換結果が空です")
                except Exception as pdf_error:
                    print(f"  PDF変換エラー: {pdf_error}")
                    return None
            else:
                print(f"エラー: PDFサポートが無効です。pdf2imageをインストールしてください。")
                print("  インストール方法: pip install pdf2image")
                return None
        
        # 通常の画像ファイルの処理
        else:
            print(f"画像ファイルを読み込み中: {filename}")
            img = Image.open(image_path)
            
            # RGB形式に変換（OCR処理の標準化）
            if img.mode != 'RGB':
                print(f"  画像モードを{img.mode}からRGBに変換中...")
                img = img.convert('RGB')
            
            print(f"  画像読み込み完了: サイズ={img.size}, モード={img.mode}")
            return img
            
    except Exception as e:
        print(f"エラー: 画像の読み込みに失敗しました: {filename}")
        print(f"  詳細: {str(e)}")
        return None



async def stream_generate(image=None, prompt=''):

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
    
    logits_processors = [NoRepeatNGramLogitsProcessor(ngram_size=30, window_size=90, whitelist_token_ids= {128821, 128822})] #whitelist: <td>, </td> 

    sampling_params = SamplingParams(
        temperature=0.0,
        max_tokens=8192,
        logits_processors=logits_processors,
        skip_special_tokens=False,
        # ignore_eos=False,
        
    )
    
    request_id = f"request-{int(time.time())}"

    printed_length = 0  

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
        assert False, f'prompt is none!!!'
    async for request_output in engine.generate(
        request, sampling_params, request_id
    ):
        # print(request_output)
        if request_output.outputs:
            full_text = request_output.outputs[0].text
            # print(full_text)
            new_text = full_text[printed_length:]
            # print(new_text, end='', flush=True)
            # print('test')
            printed_length = len(full_text)
            final_output = full_text
    # print('\n') 

    return final_output


def extract_deepseek_text(ocr_output: str) -> str:
    lines = ocr_output.splitlines()
    results = []

    for i, line in enumerate(lines):
        line = line.strip()

        # `<|ref|>text` がある行なら、次の行がテキスト
        if "<|ref|>text<|/ref|>" in line:
            # 次行が存在し、タグなしの純テキストなら追加
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                
                # 空行やタグ行は除外
                if next_line and not next_line.startswith("<|"):
                    results.append(next_line)

    return "\n".join(results)

if __name__ == "__main__":

    os.makedirs(OUTPUT_PATH, exist_ok=True)
    os.makedirs(f'{OUTPUT_PATH}/images', exist_ok=True)

    image = load_image(INPUT_PATH).convert('RGB')

    
    if '<image>' in PROMPT:

        image_features = DeepseekOCRProcessor().tokenize_with_images(images = [image], bos=True, eos=True, cropping=CROP_MODE)
    else:
        image_features = ''

    prompt = PROMPT

    result_out = asyncio.run(stream_generate(image_features, prompt))
    
    extracted_text = extract_deepseek_text(result_out)
    print("\n【抽出されたテキスト】\n")
    print("\n-------------------\n")
    print(extracted_text)
    print("\n-------------------\n")
    
