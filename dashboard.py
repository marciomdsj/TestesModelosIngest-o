# dashboard.py (VERSÃO COMPLETA E FUNCIONAL)

import streamlit as st
import pandas as pd
import requests
import json
import os

# --- Configuração da Página ---
st.set_page_config(
    page_title="Plataforma de Teste de Modelos de Ingestão",
    page_icon="🤖",
    layout="wide"
)

# --- Constantes e Configurações ---
# CORREÇÃO: Usando http em vez de https para o servidor local
API_URL = "http://127.0.0.1:8000"

# --- Funções de Lógica ---

def get_available_models():
    """Busca os modelos disponíveis na API."""
    try:
        response = requests.get(f"{API_URL}/models")
        response.raise_for_status()
        return response.json().get("models", [])
    except requests.exceptions.RequestException:
        # O erro já será exibido na UI principal
        return []

def run_test_on_api(file_bytes, filename, models_to_run_str, test_suite_json_str):
    """Envia os dados para a API FastAPI e retorna a resposta."""
    files_payload = {'file': (filename, file_bytes, 'application/pdf')}
    data_payload = {
        'test_suite_json': test_suite_json_str,
        'models_to_run': models_to_run_str
    }
    try:
        response = requests.post(f"{API_URL}/test/pdf", data=data_payload, files=files_payload, timeout=300)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao chamar a API: {e}")
        if e.response:
            st.error(f"Detalhes do servidor: {e.response.text}")
        return None

def process_results(api_response):
    """Transforma a resposta da API em um DataFrame Pandas e calcula métricas."""
    flat_results = []
    for model_summary in api_response.get('test_summary', []):
        model_name = model_summary['model_name']
        for result_item in model_summary['results']:
            # Estimativa de Custo
            cost = 0.00
            # Adiciona o custo do modelo + um custo pequeno para a chamada do "juiz"
            if "openai" in model_name.lower():
                cost = 0.005 + 0.0001
            
            result_item['model_name'] = model_name
            result_item['cost_usd_est'] = cost
            flat_results.append(result_item)
    
    if not flat_results:
        return pd.DataFrame(), {}

    df = pd.DataFrame(flat_results)
    df = df[['model_name', 'question', 'is_correct', 'latency_ms', 'cost_usd_est', 'expected_answer', 'actual_answer']]
    
    # Calcular métricas de resumo
    summary = {
        "accuracy": df.groupby('model_name')['is_correct'].mean().to_dict(),
        "avg_latency": df.groupby('model_name')['latency_ms'].mean().to_dict(),
        "total_cost": df.groupby('model_name')['cost_usd_est'].sum().to_dict()
    }
    return df, summary

def style_dataframe(df):
    """Aplica formatação condicional no DataFrame para melhor visualização."""
    return df.style.applymap(
        lambda val: 'background-color: #d4edda' if val else 'background-color: #f8d7da',
        subset=['is_correct']
    ).format({
        'latency_ms': '{:.0f} ms',
        'cost_usd_est': '$ {:.5f}'
    })

# --- Interface do Usuário (UI) ---
st.title("🤖 Plataforma de Teste de Modelos de Ingestão")
st.markdown("Faça o upload de um PDF, defina as perguntas e compare o desempenho de diferentes modelos de IA.")

# Dividir a tela em duas colunas: Configuração | Resultados
col1, col2 = st.columns([1, 2]) # Coluna de resultado maior

with col1:
    st.header("1. Configuração do Teste")
    uploaded_file = st.file_uploader("Faça o upload do seu arquivo PDF", type="pdf")
    
    available_models = get_available_models()
    if not available_models:
        st.error("Não foi possível conectar à API. Verifique se o servidor FastAPI está rodando.")
        selected_models = []
    else:
        selected_models = st.multiselect(
            "Selecione os modelos para o teste",
            options=available_models,
            default=available_models
        )
    
    st.subheader("Defina as Perguntas e Respostas Esperadas")
    gabarito_template = pd.DataFrame([
        {"pergunta": "Qual o CNPJ da empresa?", "resposta_esperada": "12.345.678/0001-99"},
        {"pergunta": "Qual o valor total?", "resposta_esperada": "R$ 1.500,00"},
    ])
    gabarito_df = st.data_editor(
        gabarito_template,
        num_rows="dynamic",
        width='stretch',
        column_config={
            "pergunta": st.column_config.TextColumn(width="large"),
            "resposta_esperada": st.column_config.TextColumn(width="large"),
        }
    )
    
    run_button = st.button("🚀 Executar Teste", width='stretch', type="primary")

with col2:
    st.header("2. Resultados da Análise")
    results_container = st.container(border=True)

# --- Lógica de Execução ---
if run_button:
    # 1. Validação dos inputs
    if not uploaded_file:
        st.warning("Por favor, faça o upload de um arquivo PDF.")
    elif not selected_models:
        st.warning("Por favor, selecione pelo menos um modelo.")
    elif gabarito_df.empty or gabarito_df['pergunta'].iloc[0] == "":
        st.warning("Por favor, adicione pelo menos uma pergunta ao gabarito.")
    else:
        with st.spinner("Analisando o documento com os modelos selecionados... Isso pode levar alguns minutos."):
            # 2. Preparação dos dados para a API
            file_bytes = uploaded_file.getvalue()
            models_str = ",".join(selected_models)
            
            # Converte o DataFrame para o formato JSON esperado pela API
            gabarito_api_format = gabarito_df.rename(columns={
                "pergunta": "question",
                "resposta_esperada": "answer"
            }).to_dict(orient='records')
            gabarito_json_str = json.dumps({"questions": gabarito_api_format})

            # 3. Chamada à API
            api_response = run_test_on_api(file_bytes, uploaded_file.name, models_str, gabarito_json_str)

            # 4. Processamento e Exibição dos Resultados
            if api_response:
                df, summary = process_results(api_response)
                
                with results_container:
                    st.subheader(f"Resumo Comparativo para: `{api_response['filename']}`")
                    
                    # --- CORREÇÃO APLICADA AQUI ---
                    # Itera sobre os modelos PRESENTES no resultado, não nos selecionados.
                    model_names_in_results = summary.get("accuracy", {}).keys()
                    metric_cols = st.columns(len(model_names_in_results))

                    for i, model_name in enumerate(model_names_in_results):
                        with metric_cols[i]:
                            st.metric(
                                label=f"🎯 Precisão - {model_name}",
                                value=f"{summary['accuracy'].get(model_name, 0):.1%}",
                            )
                            st.metric(
                                label=f"⏱️ Latência Média - {model_name}",
                                value=f"{summary['avg_latency'].get(model_name, 0):.0f} ms"
                            )
                            st.metric(
                                label=f"💰 Custo Total - {model_name}",
                                value=f"$ {summary['total_cost'].get(model_name, 0):.5f}"
                            )
                    
                    st.divider()
                    st.subheader("Resultados Detalhados")
                    st.dataframe(style_dataframe(df), use_container_width=True)
                    
                    with st.expander("Ver resposta completa da API (JSON)"):
                        st.json(api_response)