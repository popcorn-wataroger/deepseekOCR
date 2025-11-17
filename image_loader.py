"""
画像読み込みモジュール
画像ファイルやPDFファイルを読み込んでPIL Imageオブジェクトとして返す
"""

import os
import tempfile
from typing import Optional
from PIL import Image
from fastapi import HTTPException
from pdf2image import convert_from_path

# 対応する画像ファイルの拡張子
SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.pdf')


def load_image_from_file(file_content: bytes, filename: str) -> Optional[Image.Image]:
    """
    アップロードされたファイルから画像を読み込む
    
    Args:
        file_content: ファイルのバイナリコンテンツ
        filename: ファイル名
        
    Returns:
        PIL.Image.Image: 読み込んだ画像（RGB形式）
        
    Raises:
        HTTPException: ファイル形式が非対応、または読み込みに失敗した場合
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
            print(f"PDFファイルを画像に変換中: {filename}")
            
            # 一時ファイルに保存してPDF変換
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(file_content)
                temp_path = temp_file.name

            try:
                # PDFの最初のページを画像として変換（300 DPIで高品質変換）
                images = convert_from_path(
                    temp_path,
                    first_page=1,
                    last_page=1,
                    dpi=300,
                    fmt='RGB'
                )
                if images:
                    img = images[0]
                    print(f"  PDF変換完了: サイズ={img.size}, モード={img.mode}, DPI=300")
                    return img
                else:
                    raise Exception("PDFファイルの変換結果が空です")
            finally:
                # 一時ファイルを削除
                os.unlink(temp_path)

        # 通常の画像ファイルの処理
        else:
            print(f"画像ファイルを読み込み中: {filename}")
            
            import io
            img = Image.open(io.BytesIO(file_content))

            # RGB形式に変換（OCR処理の標準化）
            if img.mode != 'RGB':
                print(f"  画像モードを{img.mode}からRGBに変換中...")
                img = img.convert('RGB')

            print(f"  画像読み込み完了: サイズ={img.size}, モード={img.mode}")
            return img

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"画像の読み込みに失敗しました: {str(e)}"
        )
