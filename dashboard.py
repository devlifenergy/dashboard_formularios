# dashboard_v2.py
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
        # Ignora abas de observações ou outras abas não relevantes
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
    
    # Limpeza e formatação dos dados
    consolidated_df['Data'] = pd.to_datetime(consolidated_df['Data'], errors='coerce', dayfirst=True)
    consolidated_df = consolidated_df.dropna(subset=['Data'])

    return consolidated_df

# --- INÍCIO DA APLICAÇÃO ---
st.title("📊 Dashboard de Análise de Respostas")

spreadsheet = connect_to_gsheet()
df = load_all_data(spreadsheet)

if df.empty:
    st.warning("Não foi possível carregar nenhum dado das planilhas. Verifique se as abas de resposta contêm dados e cabeçalhos.")
    st.stop()

# --- BARRA LATERAL DE FILTROS (MODIFICADA) ---
st.sidebar.header("Filtros")

# Filtro por Respondente
lista_respondentes = df['Respondente'].dropna().unique().tolist()
respondentes_selecionados = st.sidebar.multiselect("Filtrar por Respondente:", options=lista_respondentes)

# Filtro por Data
min_date = df['Data'].min().date()
max_date = df['Data'].max().date()
data_selecionada = st.sidebar.date_input(
    "Filtrar por Período:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Filtro por Dimensão (agora com multiselect)
lista_dimensoes = df['Dimensão'].dropna().unique().tolist()
dimensoes_selecionadas = st.sidebar.multiselect("Filtrar por Dimensão (opcional):", options=lista_dimensoes)


# --- APLICAÇÃO DOS FILTROS ---
df_filtrado = df.copy()

# Aplica filtro de data
if len(data_selecionada) == 2:
    start_date, end_date = data_selecionada
    df_filtrado = df_filtrado[df_filtrado['Data'].dt.date.between(start_date, end_date)]

# Aplica filtro de respondente
if respondentes_selecionados:
    df_filtrado = df_filtrado[df_filtrado['Respondente'].isin(respondentes_selecionados)]
    
# Aplica filtro de dimensão
if dimensoes_selecionadas:
    df_filtrado = df_filtrado[df_filtrado['Dimensão'].isin(dimensoes_selecionadas)]


# --- EXIBIÇÃO DOS RESULTADOS (MODIFICADO) ---
st.header("Distribuição Geral das Respostas")

if df_filtrado.empty:
    st.info("Nenhuma resposta encontrada para os filtros selecionados.")
else:
    # Contagem de todas as respostas no DataFrame filtrado
    contagem_respostas = df_filtrado['Resposta'].value_counts()
    
    # Criação do gráfico de pizza
    st.subheader("Gráfico de Respostas Agregadas")
    fig, ax = plt.subplots()
    
    ax.pie(
        contagem_respostas,
        labels=contagem_respostas.index,
        autopct='%1.1f%%',
        startangle=90,
        pctdistance=0.85
    )
    ax.axis('equal')

    centre_circle = plt.Circle((0,0),0.70,fc='white')
    fig.gca().add_artist(centre_circle)
    
    st.pyplot(fig)

# Exibição dos dados brutos filtrados
with st.expander("Ver dados filtrados"):
    st.dataframe(df_filtrado)