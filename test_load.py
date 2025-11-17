from PIL import Image
import os
INPUT_PATH = './testdata/inputs/receipt_000112.pdf'
OUTPUT_PATH = './testdata/outputs/'
CROP_MODE = True
PROMPT = '<image>\n<|grounding|>Convert the document to markdown.'
SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.pdf') # 対応する画像ファイルの拡張子（大文字小文字両対応）

# PDF処理のインポート（オプション）
try:
    from pdf2image import convert_from_path
    PDF_SUPPORT = True
    print("PDF処理サポートが有効です。")
except ImportError:
    PDF_SUPPORT = False
    print("警告: pdf2imageが見つかりません。PDFファイルは処理できません。")

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


image = load_image(INPUT_PATH).convert('RGB')