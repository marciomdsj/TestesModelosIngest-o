import requests
import json
import time
import os
# --- CONFIGURAÇÃO ---
API_URL = "http://127.0.0.1:8000/test/pdf"
MODELS_TO_RUN = ["local_ocr", "openai_gpt4o"] #Adicionar mais modelos caso queira

# # Adicione um dicionário para cada PDF que você quer testar.
# Preencha o 'pdf_path' e as 'questions' para cada um.
# -----------------------------------------------------------
TEST_SUITE = [
    {
        "pdf_path": "tests/Smart-Fita-LED-RGB-Wi-Fi-2-Geração.pdf",
        "questions": [
            {"question": "Quantas cores ela possui?", "answer": "16 milhões de cores"},
            {"question": "Com quais sistemas ela é compatível?", "answer": "Amazon Alexa e Google Assistente"},
            {"question": "O que vem dentro da embalagem?", "answer": "1 Smart Fita LED RGB wifi, fonte de almientação, controladora, conector e guia rápido de instalação"}
        ]
    },
    {
        "pdf_path": "tests/AF_GUIARAPIDO_SmartRobo-Wi-Fi+.pdf",
        "questions": [
            {
                "question": "Como parear?", 
                # --- CORREÇÃO APLICADA AQUI ---
                # A resposta foi transformada em uma única linha para evitar erros de formatação no envio.
                "answer": "Vá até a loja de aplicativos do seu smartphone e procure pelo aplicativo Positivo Casa Inteligente (disponível no Google Play e APP Store) e instale gratuitamente. Caso seu Robô aspirador não esteja em modo de pareamento, pressione e segure o botão de limpeza em modo espiral por até 5 segundos, o robô emitirá 2 beeps e uma luz piscará indicando o modo de pareamento. Escolha na lista o Smart Robô Aspirador + e siga os passos do aplicativo para inserir a senha da rede Wi-Fi na qual deseja se conectar e pronto! É só aguardar."
            },
            {"question": "Quais são os padrões de limpeza?", "answer": "Espiral, Limpeza de cantos, Modo inteligente e modo zigue-zague."},
            {"question": "Qual o nome do componente indicado pelo número 5 na vista inferior?", "answer": "Sensores anti-queda"},
            {"question": "Na imagem, como se chama o item de número 14?", "answer": "Filtro HEPA"},
            {"question": "O que é o componente número 8, localizado na parte de baixo do robô?", "answer": "Canal de sucção"}
        ]
    },
    {
        "pdf_path": "tests/Smart-Interruptor-Wi-Fi-2-Canais.pdf",
        "questions": [
            # A vírgula extra no final foi removida
            {"question": "Qual o conteúdo da embalagem?", "answer": "1X Smart Interruptor Wi-Fi e guia rápido de instalação."}
        ]
    },
    {
        "pdf_path": "tests/Smart-Luminária-de-Mesa-Wi-Fi.pdf",
        "questions": [
            # A vírgula extra no final foi removida
            {"question": "Qual a garantia do produto?", "answer": "1 ano"}
        ]
    }
]
# -----------------------------------------------------------

def run_single_test(pdf_path, questions, models):
    """Função que chama a API para um único PDF."""
    print(f"\n--- 🧪 Iniciando teste para: {pdf_path} ---")
    
    test_suite_payload = {"questions": questions}
    
    # --- MUDANÇA AQUI ---
    # Agora 'data' é um dicionário simples, que é mais robusto para o 'requests'.
    data_payload = {
        'test_suite_json': json.dumps(test_suite_payload),
        'models_to_run': ",".join(models)
    }
    
    try:
        with open(pdf_path, 'rb') as pdf_file:
            # O arquivo é passado pelo parâmetro 'files', e os outros dados pelo parâmetro 'data'.
            files_payload = {'file': (os.path.basename(pdf_path), pdf_file, 'application/pdf')}
            response = requests.post(API_URL, data=data_payload, files=files_payload, timeout=300)
            response.raise_for_status()
            print(f"--- ✅ Teste para {pdf_path} concluído com sucesso! ---")
            return response.json()
    except FileNotFoundError:
        print(f"--- ❌ ERRO: Arquivo não encontrado em '{pdf_path}'. Pulando este teste. ---")
        return None
    except requests.exceptions.RequestException as e:
        print(f"--- ❌ ERRO ao chamar a API para {pdf_path}: {e} ---")
        # Esta parte agora deve mostrar um erro mais detalhado do servidor, se houver.
        if e.response:
            print(f"Detalhes: {e.response.text}")
        return None

def main():
    """Função principal que executa todos os testes e salva o resultado."""
    all_results = []
    start_time = time.time()
    
    for test_case in TEST_SUITE:
        result = run_single_test(
            pdf_path=test_case["pdf_path"],
            questions=test_case["questions"],
            models=MODELS_TO_RUN
        )
        if result:
            all_results.append(result)

    end_time = time.time()
    total_duration = end_time - start_time

    # Salva todos os resultados em um único arquivo JSON
    output_filename = "resultados_completos.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
        
    print("\n=======================================================")
    print(f"🏁 Todos os testes foram concluídos em {total_duration:.2f} segundos.")
    print(f"📄 Os resultados completos foram salvos em: {output_filename}")
    print("=======================================================")

if __name__ == "__main__":
    main()