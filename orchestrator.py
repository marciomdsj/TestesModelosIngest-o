import time
from models.base_model import IngestionModel
from typing import List, Dict, Any
from openai import OpenAI
import os
import json

class PDFTestOrchestrator:
    def __init__(self, models: List[IngestionModel]):
        self.models = models
        self.judge_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def _get_ai_judge_evaluation(self, question, expected_answer, actual_answer) -> bool:
        """Usa um LLM para avaliar semanticamente se a resposta obtida é correta."""
        if not actual_answer or "erro" in actual_answer.lower():
            return False

        # Para respostas curtas, uma verificação simples pode ser suficiente e mais barata
        if len(expected_answer) < 20 and expected_answer.lower() in actual_answer.lower():
            return True

        prompt = f"""
        Você é um juiz de IA avaliando a qualidade da resposta de outro modelo.
        Sua tarefa é determinar se a "Resposta Obtida" é uma resposta semanticamente correta para a "Pergunta", comparando-a com a "Resposta Esperada" (gabarito).

        A "Resposta Obtida" não precisa ser idêntica à "Resposta Esperada". Ela pode ser um resumo, uma parafrase, ou conter informações adicionais, desde que o cerne da resposta esteja correto.

        Pergunta: "{question}"
        Resposta Esperada (Gabarito): "{expected_answer}"
        Resposta Obtida (para ser avaliada): "{actual_answer}"

        A "Resposta Obtida" está correta? Responda apenas com a palavra "Sim" ou "Não".
        """
        try:
            response = self.judge_client.chat.completions.create(
                model="gpt-4o", # Poderia ser um modelo mais barato como gpt-3.5-turbo
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
                temperature=0.0,
            )
            decision = response.choices[0].message.content.strip().lower()
            return "sim" in decision
        except Exception:
            # Em caso de falha do juiz, recorre à verificação simples
            return (expected_answer or "").lower() in (actual_answer or "").lower()

    def run_tests(self, pdf_path: str, test_questions: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        final_results = []
        
        for model in self.models:
            model_results = []
            for item in test_questions:
                question = item.get("question")
                expected_answer = item.get("answer")
                
                start_time = time.time()
                try:
                    actual_answer = model.ingest_and_query(pdf_path, question)
                except Exception as e:
                    actual_answer = f"ERRO: {str(e)}"
                end_time = time.time()
                
                latency = (end_time - start_time) * 1000
                
                # --- NOVA AVALIAÇÃO COM "IA COMO JUIZ" ---
                is_correct = self._get_ai_judge_evaluation(question, expected_answer, actual_answer)
                
                result = {
                    "question": question,
                    "expected_answer": expected_answer,
                    "actual_answer": actual_answer,
                    "latency_ms": round(latency),
                    "is_correct": is_correct
                }
                model_results.append(result)
            
            final_results.append({
                "model_name": model.model_name,
                "results": model_results
            })
        
        return final_results