#Ideia: Todos os modelos devem herdar uma classe base que define o contrato

from abc import ABC, abstractmethod

class IngestionModel(ABC):
    """
    Interface abstrata para todos os modelos de ingestão de pdf
    """
    def __init__(self, model_name: str):
        self.model_name = model_name

        @abstractmethod
        def ingest_and_query(self, pdf_path: str, query: str) -> str:
            """
            Recebe o caminho de um PDF e uma pergunta, retorna a resposta como string
            """
            pass

        def __str__(self):
            return self.model_name