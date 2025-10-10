# dashboard_v6.py
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

# --- LISTA MESTRA DE TODAS AS PERGUNTAS ---
@st.cache_data
def carregar_itens_master():
    """Retorna um DataFrame com todos os itens de todos os formulários e seu status de reverso."""
    # IMPORTANTE: Você precisa preencher esta lista com os itens de TODOS os seus formulários.
    # Adicionei apenas alguns exemplos para a lógica funcionar.
    todos_os_itens = [
        ('IF01', 'Instalações Físicas', 'O espaço físico é suficiente...', 'NÃO'),
        ('IF12', 'Instalações Físicas', 'Há obstáculos ou áreas obstruídas...', 'SIM'),
        ('EQ01', 'Equipamentos', 'Os equipamentos necessários estão disponíveis...', 'NÃO'),
        ('EQ11', 'Equipamentos', 'Paradas não planejadas atrapalham...', 'SIM'),
        ('FE01', 'Ferramentas', 'As ferramentas necessárias estão disponíveis...', 'NÃO'),
        ('FE08', 'Ferramentas', 'Ferramentas compartilhadas raramente estão...', 'SIM'),
        ('PT01', 'Postos de Trabalho', 'O posto permite ajuste ergonômico...', 'NÃO'),
        ('PT10', 'Postos de Trabalho', 'O desenho do posto induz posturas forçadas...', 'SIM'),
        ('RN01', 'Regras e Normas', 'As regras da empresa são claras...', 'NÃO'),
        ('PI02', 'Práticas Informais', 'A cultura do “jeitinho”...', 'NÃO'),
        ('RE01', 'Recompensas e Benefícios', 'A política de recompensas e benefícios é justa...', 'NÃO'),
        ('EX01', 'Fatores de Risco (Reversos)', 'Sacrifico frequentemente minha vida pessoal...', 'SIM'),
        ('CU01', 'Cultura Organizacional', 'As práticas diárias refletem...', 'NÃO'),
        ('FRPS01', 'Fatores de Risco Psicossocial (FRPS)', 'No meu ambiente há piadas...', 'SIM'),
        # ... (continue adicionando todos os outros itens aqui) ...
    ]
    df_master = pd.DataFrame(todos_os_itens, columns=["ID_Item", "Dimensão", "Item", "Reverso"])
    # O dashboard usa a coluna 'Item' para fazer a correspondência.
    return df_master

# --- CONEXÃO COM GOOGLE SHEETS E CARREGAMENTO DE DADOS ---
@st.cache_resource
def connect_to_gsheet():
    creds_dict = dict(st.secrets["google_credentials"])
    creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
    gc = gspread.service_account_from_dict(creds_dict)
    spreadsheet = gc.open("Respostas Formularios")
    return spreadsheet

@st.cache_data(ttl=600)
def load_all_data(_spreadsheet, _df_master):
    if _spreadsheet is None: return pd.DataFrame()
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
    if not all_dfs: return pd.DataFrame()
    consolidated_df = pd.concat(all_dfs, ignore_index=True)
    
    # Junta com a lista mestra para obter o status 'Reverso' de cada item
    consolidated_df = pd.merge(consolidated_df, _df_master[['Item', 'Reverso']], on='Item', how='left')
    
    consolidated_df['Resposta_Num'] = pd.to_numeric(consolidated_df['Resposta'], errors='coerce')
    
    def ajustar_reverso(row):
        if pd.isna(row['Resposta_Num']): return None
        return (6 - row['Resposta_Num']) if row['Reverso'] == 'SIM' else row['Resposta_Num']
        
    consolidated_df['Pontuação'] = consolidated_df.apply(ajustar_reverso, axis=1)

    consolidated_df['Data'] = pd.to_datetime(consolidated_df['Data'], errors='coerce', dayfirst=True)
    consolidated_df = consolidated_df.dropna(subset=['Data'])
    return consolidated_df

# --- INÍCIO DA APLICAÇÃO ---
st.title("📊 Dashboard de Análise de Respostas")

df_master_itens = carregar_itens_master()
spreadsheet = connect_to_gsheet()
df = load_all_data(spreadsheet, df_master_itens)

if df.empty:
    st.warning("Não foi possível carregar ou processar dados das planilhas.")
    st.stop()

# --- BARRA LATERAL DE FILTROS ---
st.sidebar.header("Filtros")
lista_respondentes = df['Respondente'].dropna().unique().tolist()
respondentes_selecionados = st.sidebar.multiselect("Filtrar por Respondente:", options=lista_respondentes)

min_date = df['Data'].min().date()
max_date = df['Data'].max().date()
data_selecionada = st.sidebar.date_input(
    "Filtrar por Período:", value=(min_date, max_date),
    min_value=min_date, max_value=max_date
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
st.header("Análise de Desempenho por Dimensão")

if df_filtrado.empty:
    st.info("Nenhuma resposta encontrada para os filtros selecionados.")
else:
    resumo_dimensoes = df_filtrado.groupby('Dimensão')['Pontuação'].mean().round(2).reset_index()
    resumo_dimensoes = resumo_dimensoes.rename(columns={'Pontuação': 'Média'}).sort_values('Média', ascending=False)
    
    if resumo_dimensoes.empty or resumo_dimensoes['Média'].isnull().all():
        st.info("Nenhuma resposta válida para gerar a análise por dimensão.")
    else:
        st.subheader("Pontuação Média por Dimensão")
        st.dataframe(resumo_dimensoes, use_container_width=True, hide_index=True)

        # ##### TRECHO DO GRÁFICO ALTERADO PARA PIZZA COM LEGENDA NUMERADA #####
        st.subheader("Gráfico Comparativo por Dimensão")

        # Dados para o gráfico
        labels = resumo_dimensoes["Dimensão"]
        values = resumo_dimensoes["Média"]
        slice_labels = [str(i+1) for i in range(len(labels))] # Cria rótulos "1", "2", "3"...

        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Cria a pizza usando os valores como tamanho e os números como rótulo de cada fatia
        wedges, texts = ax.pie(
            values, 
            labels=slice_labels, 
            startangle=90,
            textprops=dict(color="w", size=12, weight="bold") # Estilo dos números
        )
        ax.axis('equal')
        
        st.pyplot(fig)

        # Cria a legenda numerada abaixo do gráfico
        st.subheader("Legenda do Gráfico")
        for i, row in resumo_dimensoes.iterrows():
            st.markdown(f"**{i+1}:** {row['Dimensão']} (Média: **{row['Média']:.2f}**)")
        # --- FIM DO TRECHO ALTERADO ---

# Expander com dados brutos
with st.expander("Ver dados filtrados"):
    st.dataframe(df_filtrado)