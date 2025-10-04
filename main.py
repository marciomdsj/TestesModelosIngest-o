# main.py (VERSÃO CORRIGIDA)

import os
import json
import tempfile
from typing import List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import ValidationError

from orchestrator import PDFTestOrchestrator
from schemas import TestSummaryResponse
from models.local_ocr_model import LocalOCRModel
from models.openai_vision_model import OpenAIVisionModel
from dotenv import load_dotenv
load_dotenv()

# --- Configuração da Aplicação ---
app = FastAPI(
    title="Módulo de Teste de Ingestão de PDF",
    description="Uma API para comparar o desempenho de diferentes modelos de IA na extração de dados e Q&A de PDFs.",
    version="1.0.0"
)

# --- Instância dos Modelos ---
AVAILABLE_MODELS = {
    "local_ocr": LocalOCRModel(),
    "openai_gpt4o": OpenAIVisionModel(model_name="gpt-4o")
}

# --- Endpoint Principal ---
@app.post("/test/pdf", response_model=TestSummaryResponse, tags=["PDF Testing"])
async def run_pdf_test(
    file: UploadFile = File(..., description="Arquivo PDF a ser testado."),
    test_suite_json: str = Form(..., description='JSON string contendo uma lista de objetos com "question" e "answer".'),
    models_to_run: str = Form(..., description="String com nomes dos modelos separados por vírgula. Ex: 'local_ocr,openai_gpt4o'")
):
    """
    Recebe um PDF, um conjunto de perguntas/respostas e uma lista de modelos.
    Executa os testes e retorna um resumo comparativo.
    """
    # --- MUDANÇA AQUI ---
    # Convertemos a string recebida em uma lista de nomes de modelos.
    model_name_list = [name.strip() for name in models_to_run.split(',')]

    # Validação dos modelos solicitados
    selected_models = []
    for model_name in model_name_list:
        if model_name not in AVAILABLE_MODELS:
            raise HTTPException(
                status_code=400, 
                detail=f"Modelo '{model_name}' não é válido. Modelos disponíveis: {list(AVAILABLE_MODELS.keys())}"
            )
        selected_models.append(AVAILABLE_MODELS[model_name])

    # Validação do JSON da suíte de testes
    try:
        test_suite = json.loads(test_suite_json)
        questions = test_suite.get("questions", [])
        if not questions:
            raise ValueError("A chave 'questions' não pode estar vazia no JSON.")
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"JSON da suíte de testes inválido: {e}")

    # Salva o arquivo temporariamente
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_pdf_path = temp_file.name

    try:
        # Executa a orquestração
        orchestrator = PDFTestOrchestrator(models=selected_models)
        results = orchestrator.run_tests(temp_pdf_path, questions)
        
        return {
            "filename": file.filename,
            "filesize_bytes": len(content),
            "test_summary": results
        }
    finally:
        # Garante que o arquivo temporário seja deletado
        os.unlink(temp_pdf_path)

@app.get("/models", tags=["Configuration"])
async def get_available_models():
    """Retorna a lista de modelos de ingestão disponíveis para teste."""
    return {"models": list(AVAILABLE_MODELS.keys())}