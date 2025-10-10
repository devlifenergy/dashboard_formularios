# dashboard_v4.py
import streamlit as st
import pandas as pd
import gspread
import matplotlib.pyplot as plt
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Dashboard de Resultados - Lifenergy",
    layout="wide"
)

# --- CONEXÃO COM GOOGLE SHEETS (COM CACHE) ---
@st.cache_resource
def connect_to_gsheet():
    """Conecta ao Google Sheets e retorna o objeto da planilha principal."""
    try:
        creds_dict = dict(st.secrets["google_credentials"])
        creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
        gc = gspread.service_account_from_dict(creds_dict)
        spreadsheet = gc.open("Respostas Formularios")
        return spreadsheet
    except Exception as e:
        st.error(f"Erro ao conectar com o Google Sheets: {e}")
        return None

# --- CARREGAMENTO E CONSOLIDAÇÃO DOS DADOS (COM CACHE) ---
@st.cache_data(ttl=600) # Atualiza os dados a cada 10 minutos
def load_all_data(_spreadsheet):
    """Carrega os dados de todas as abas de resposta e os consolida."""
    if _spreadsheet is None:
        return pd.DataFrame()

    worksheets = _spreadsheet.worksheets()
    all_dfs = []
    
    for ws in worksheets:
        if "observacoes" not in ws.title.lower() and "teste" not in ws.title.lower():
            try:
                data = ws.get_all_records()
                if data:
                    df = pd.DataFrame(data)
                    all_dfs.append(df)
            except Exception as e:
                st.warning(f"Não foi possível ler a aba '{ws.title}': {e}")

    if not all_dfs:
        return pd.DataFrame()

    consolidated_df = pd.concat(all_dfs, ignore_index=True)
    
    consolidated_df['Resposta'] = consolidated_df['Resposta'].astype(str).str.strip()
    consolidated_df['Data'] = pd.to_datetime(consolidated_df['Data'], errors='coerce', dayfirst=True)
    consolidated_df = consolidated_df.dropna(subset=['Data'])

    return consolidated_df

# --- INÍCIO DA APLICAÇÃO ---
st.title("📊 Dashboard de Análise de Respostas")

spreadsheet = connect_to_gsheet()
df = load_all_data(spreadsheet)

if df.empty:
    st.warning("Não foi possível carregar nenhum dado das planilhas.")
    st.stop()

# --- BARRA LATERAL DE FILTROS ---
st.sidebar.header("Filtros")

lista_respondentes = df['Respondente'].dropna().unique().tolist()
respondentes_selecionados = st.sidebar.multiselect("Filtrar por Respondente:", options=lista_respondentes)

min_date = df['Data'].min().date()
max_date = df['Data'].max().date()
data_selecionada = st.sidebar.date_input(
    "Filtrar por Período:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

lista_dimensoes = df['Dimensão'].dropna().unique().tolist()
dimensoes_selecionadas = st.sidebar.multiselect("Filtrar por Dimensão (opcional):", options=lista_dimensoes)


# --- APLICAÇÃO DOS FILTROS ---
df_filtrado = df.copy()

if len(data_selecionada) == 2:
    start_date, end_date = data_selecionada
    df_filtrado = df_filtrado[df_filtrado['Data'].dt.date.between(start_date, end_date)]

if respondentes_selecionados:
    df_filtrado = df_filtrado[df_filtrado['Respondente'].isin(respondentes_selecionados)]
    
if dimensoes_selecionadas:
    df_filtrado = df_filtrado[df_filtrado['Dimensão'].isin(dimensoes_selecionadas)]


# --- EXIBIÇÃO DOS RESULTADOS ---
st.header("Distribuição Geral das Respostas")

if df_filtrado.empty:
    st.info("Nenhuma resposta encontrada para os filtros selecionados.")
else:
    respostas_validas = ['1', '2', '3', '4', '5', 'N/A']
    df_respostas_para_grafico = df_filtrado[df_filtrado['Resposta'].isin(respostas_validas)]
    
    if df_respostas_para_grafico.empty:
        st.info("Nenhuma resposta válida (1-5 ou N/A) encontrada para os filtros selecionados.")
    else:
        contagem_respostas = df_respostas_para_grafico['Resposta'].value_counts()
        
        ordem_labels = [str(i) for i in range(1, 6)] + ['N/A']
        contagem_respostas = contagem_respostas.reindex(ordem_labels, fill_value=0)
        contagem_respostas = contagem_respostas[contagem_respostas > 0]

        if not contagem_respostas.empty:
            st.subheader("Gráfico de Respostas Agregadas")
            
            # ##### TRECHO DO GRÁFICO ALTERADO #####
            fig, ax = plt.subplots(figsize=(8, 8))
            
            # Extrai os labels (1, 2, 3...) e os valores (contagens)
            labels = contagem_respostas.index
            sizes = contagem_respostas.values
            
            # Gera o gráfico de pizza apenas com as porcentagens
            wedges, texts, autotexts = ax.pie(
                sizes, 
                autopct='%1.1f%%',
                startangle=90,
                pctdistance=0.85, # Distância do centro para as porcentagens
                wedgeprops=dict(width=0.4) # Para criar o efeito "donut"
            )

            # Adiciona um círculo no centro para o efeito "donut"
            centre_circle = plt.Circle((0,0),0.70,fc='white')
            fig.gca().add_artist(centre_circle)
            
            # Loop para adicionar o NÚMERO da categoria junto com a porcentagem
            for i, autotext in enumerate(autotexts):
                percentage = autotext.get_text()
                category_label = labels[i]
                autotext.set_text(f"{category_label}\n{percentage}") # Ex: "5\n30.0%"
                autotext.set_fontsize(12)
                autotext.set_fontweight('bold')

            ax.axis('equal')
            st.pyplot(fig)

            # --- Legenda Separada Abaixo do Gráfico ---
            st.subheader("Legenda")
            legend_data = {
                '1': 'Discordo totalmente',
                '2': 'Discordo parcialmente',
                '3': 'Neutro',
                '4': 'Concordo parcialmente',
                '5': 'Concordo totalmente',
                'N/A': 'Não se aplica'
            }
            
            legend_html = "<div style='display: flex; flex-wrap: wrap; justify-content: center;'>"
            for label_key in ordem_labels:
                if label_key in contagem_respostas.index:
                    legend_html += f"<div style='margin: 5px 15px;'><b>{label_key}:</b> {legend_data.get(label_key, '')}</div>"
            legend_html += "</div>"
            st.markdown(legend_html, unsafe_allow_html=True)


# Exibição dos dados brutos filtrados
with st.expander("Ver dados filtrados"):
    st.dataframe(df_filtrado)