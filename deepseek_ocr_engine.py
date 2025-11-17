"""
DeepSeek OCRエンジンモジュール
OCRモデルの初期化と推論処理を管理
"""

import os
import sys
import time
from typing import Optional
import torch

# DeepSeek-OCRのモジュールパスを追加
sys.path.insert(0, '/DeepSeek-OCR/DeepSeek-OCR-master/DeepSeek-OCR-vllm')

if torch.version.cuda == '11.8':
    os.environ["TRITON_PTXAS_PATH"] = "/usr/local/cuda-11.8/bin/ptxas"

os.environ['VLLM_USE_V1'] = '0'
os.environ["CUDA_VISIBLE_DEVICES"] = '0'

from vllm import AsyncLLMEngine, SamplingParams
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.model_executor.models.registry import ModelRegistry
from deepseek_ocr import DeepseekOCRForCausalLM
from PIL import Image
from process.ngram_norepeat import NoRepeatNGramLogitsProcessor
from process.image_process import DeepseekOCRProcessor
from fastapi import HTTPException

ModelRegistry.register_model("DeepseekOCRForCausalLM", DeepseekOCRForCausalLM)

# モデルパス
MODEL_PATH = 'deepseek-ai/DeepSeek-OCR'


class DeepSeekOCREngine:
    """
    DeepSeek OCRエンジンクラス
    OCRモデルの初期化と推論を管理するシングルトンクラス
    """
    
    def __init__(self):
        self.engine: Optional[AsyncLLMEngine] = None
        self.processor = DeepseekOCRProcessor()
    
    async def initialize(self):
        """
        OCRエンジンを初期化
        """
        if self.engine is not None:
            print("OCRエンジンは既に初期化されています")
            return
        
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
        self.engine = AsyncLLMEngine.from_engine_args(engine_args)
        print("OCRエンジンの初期化が完了しました")
    
    def shutdown(self):
        """
        エンジンのシャットダウン処理
        """
        if self.engine is not None:
            self.engine = None
            print("OCRエンジンをシャットダウンしました")
    
    def is_initialized(self) -> bool:
        """
        エンジンが初期化されているかチェック
        
        Returns:
            bool: 初期化されている場合True
        """
        return self.engine is not None
    
    def preprocess_image(self, image: Image.Image, crop_mode: bool = True) -> dict:
        """
        画像を前処理してOCRエンジン用の特徴量に変換
        
        Args:
            image: PIL Image オブジェクト
            crop_mode: クロップモードを有効にするか
            
        Returns:
            dict: 画像特徴量
        """
        image_features = self.processor.tokenize_with_images(
            images=[image],
            bos=True,
            eos=True,
            cropping=crop_mode
        )
        return image_features
    
    async def generate(self, image_features=None, prompt: str = '') -> str:
        """
        OCRモデルでテキストを生成
        
        Args:
            image_features: 前処理された画像特徴量
            prompt: プロンプト文字列
            
        Returns:
            str: OCRモデルの生出力
            
        Raises:
            HTTPException: エンジンが初期化されていない、またはプロンプトが無効な場合
        """
        if self.engine is None:
            raise HTTPException(
                status_code=503,
                detail="OCRエンジンが初期化されていません"
            )

        # LogitsProcessorの設定（繰り返しを防ぐ）
        logits_processors = [
            NoRepeatNGramLogitsProcessor(
                ngram_size=30,
                window_size=90,
                whitelist_token_ids={128821, 128822}  # <td>, </td>
            )
        ]

        # サンプリングパラメータ
        sampling_params = SamplingParams(
            temperature=0.0,
            max_tokens=8192,
            logits_processors=logits_processors,
            skip_special_tokens=False,
        )

        request_id = f"request-{int(time.time())}"

        # リクエストの構築
        if image_features and '<image>' in prompt:
            request = {
                "prompt": prompt,
                "multi_modal_data": {"image": image_features}
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

        # 推論実行
        final_output = ""
        async for request_output in self.engine.generate(
            request, sampling_params, request_id
        ):
            if request_output.outputs:
                full_text = request_output.outputs[0].text
                final_output = full_text

        return final_output
    
    @staticmethod
    def extract_text(ocr_output: str) -> str:
        """
        OCR出力からテキストを抽出
        
        Args:
            ocr_output: OCRモデルの生出力
            
        Returns:
            str: 抽出されたテキスト
        """
        lines = ocr_output.splitlines()
        results = []

        for i, line in enumerate(lines):
            line = line.strip()

            # `<|ref|>text<|/ref|>` がある行なら、次の行がテキスト
            if "<|ref|>text<|/ref|>" in line:
                # 次行が存在し、タグなしの純テキストなら追加
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()

                    # 空行やタグ行は除外
                    if next_line and not next_line.startswith("<|"):
                        results.append(next_line)

        # <|ref|>text<|/ref|>形式のタグがない場合は、raw_outputをそのまま返す
        if not results:
            return ocr_output
        
        return "\n".join(results)


# グローバルエンジンインスタンス
ocr_engine = DeepSeekOCREngine()
