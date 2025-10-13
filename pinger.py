import time
from playwright.sync_api import sync_playwright

# --- CONFIGURAÇÕES ---
# Coloque a URL completa do seu aplicativo Streamlit aqui
URL_DO_APP = "https://wedja-dashboard.streamlit.app/" 
# Coloque o texto exato do botão que você quer clicar
TEXTO_DO_BOTAO = "Finalizar e Gerar Relatório"

def ping_e_clica():
    print(f"Iniciando o ping para: {URL_DO_APP}")
    with sync_playwright() as p:
        try:
            # Inicia o navegador (headless=True roda em segundo plano, sem abrir janela)
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navega até a URL do seu app
            print("Acessando a página...")
            page.goto(URL_DO_APP, timeout=120000) # Timeout de 2 minutos para carregar
            
            # Espera um tempo extra para o Streamlit renderizar tudo
            print("Página carregada. Aguardando 10 segundos para renderização completa...")
            time.sleep(10)
            
            print("Procurando e clicando no botão de ping invisível...")
            # O seletor "#autoclick-div button" significa: encontre a div com id="autoclick-div" e clique no botão dentro dela
            page.locator("#autoclick-div button").click()
            
            # Espera mais um pouco para a ação do clique ser processada
            print("Botão clicado. Aguardando 5 segundos...")
            time.sleep(5)
            
            browser.close()
            print("Ping com clique concluído com sucesso!")

        except Exception as e:
            print(f"Ocorreu um erro: {e}")

if __name__ == "__main__":
    ping_e_clica()