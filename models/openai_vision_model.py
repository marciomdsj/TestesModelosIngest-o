import base64
import io
from openai import OpenAI
from .base_model import IngestionModel
import os
from pdf2image import convert_from_path
from PIL import Image

class OpenAIVisionModel(IngestionModel):
    def __init__(self, model_name="gpt-4o-mini"):
        super().__init__(f"OpenAI_{model_name}")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model_name

    def _convert_pdf_to_images_base64(self, pdf_path: str):
        """Converte cada página de um PDF em uma imagem base64."""
        images = convert_from_path(pdf_path)
        base64_images = []
        for image in images:
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            base64_images.append(f"data:image/jpeg;base64,{img_str}")
        return base64_images

    def ingest_and_query(self, pdf_path: str, query: str) -> str:
        try:
            base64_images = self._convert_pdf_to_images_base64(pdf_path)
            
            # Monta o payload multimodal
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""
                            Analise as imagens do documento fornecido e responda à seguinte pergunta de forma direta e precisa.
                            Pergunta: "{query}"
                            """
                        }
                    ]
                }
            ]
            
            # Adiciona cada página do PDF como uma imagem na requisição
            for img_url in base64_images:
                messages[0]["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": img_url
                    }
                })

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=300,
                temperature=0.0,
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            # Fornece um erro mais detalhado se a conversão ou a API falhar
            return f"ERRO no processamento multimodal: {str(e)}"