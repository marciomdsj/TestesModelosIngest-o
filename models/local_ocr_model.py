# models/local_ocr_model.py (VERSÃO CORRIGIDA)

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
from .base_model import IngestionModel

# Você precisa ter o Tesseract-OCR instalado no seu sistema
# sudo apt-get install tesseract-ocr tesseract-ocr-por (para português)

class LocalOCRModel(IngestionModel):
    def __init__(self):
        super().__init__("Local_PyMuPDF_Tesseract")

    def ingest_and_query(self, pdf_path: str, query: str) -> str:
        full_text = ""
        doc = fitz.open(pdf_path)

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # 1. Tenta extrair texto nativo
            text = page.get_text()
            full_text += text

            # 2. Se não houver muito texto nativo, trata a página inteira como imagem (fallback)
            if len(text.strip()) < 50: # Um limiar para considerar a página como "imagem"
                try:
                    pix = page.get_pixmap(dpi=300) # Renderiza a página com alta resolução
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    ocr_text = pytesseract.image_to_string(img, lang='por')
                    full_text += f"\n[OCR Página Completa {page_num+1}]:\n{ocr_text}"
                except Exception as e:
                    print(f"Aviso: Erro no OCR da página inteira {page_num+1}: {e}")

            # 3. Extrai imagens incorporadas (ainda útil para PDFs mistos)
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                try:
                    image = Image.open(io.BytesIO(image_bytes))
                    ocr_text = pytesseract.image_to_string(image, lang='por')
                    full_text += f"\n[OCR Imagem Incorporada {page_num+1}-{img_index+1}]:\n{ocr_text}"
                except Exception as e:
                    print(f"Aviso: Erro no OCR da imagem incorporada {img_index+1}: {e}")
        
        return full_text