import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Configuração de logging para reduzir mensagens excessivas
logging.basicConfig(level=logging.INFO)

# Configuração das opções do ChromeDriver
options = Options()
options.add_argument("--headless")  # Modo headless (sem interface gráfica)
options.add_argument("--no-sandbox")  # Necessário em ambientes restritos
options.add_argument("--disable-dev-shm-usage")  # Evita problemas de memória compartilhada
options.add_argument("--disable-gpu")  # Desativa GPU
options.add_argument("--disable-extensions")  # Desativa extensões
options.add_argument("--remote-debugging-port=9222")  # Resolve conflitos de porta
options.add_argument("--window-size=1920,1080")  # Define um tamanho de janela padrão
options.add_argument("--disable-software-rasterizer")  # Melhora desempenho
options.add_argument("--disable-setuid-sandbox")  # Adicional para segurança

# Configuração global do ChromeDriverManager
CHROME_DRIVER_PATH = ChromeDriverManager().install()

def scrape_price(url):
    """
    Faz a raspagem de preços de um produto dado o URL.
    """
    try:
        logging.info(f"Iniciando raspagem para URL: {url}")
        # Inicializa o driver do navegador
        driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)
        driver.get(url)

        # Aguarda o carregamento da página
        driver.implicitly_wait(10)

        # Recupera informações do produto
        name = driver.find_element(By.ID, "productTitle").text.strip()
        price_whole = driver.find_element(By.CSS_SELECTOR, "span.a-price-whole").text
        price_fraction = driver.find_element(By.CSS_SELECTOR, "span.a-price-fraction").text
        price = float(f"{price_whole}.{price_fraction}".replace(",", ""))

        driver.quit()
        return name, price
    except Exception as e:
        logging.error(f"Erro ao processar a URL: {url} | Erro: {e}")
        return None, None
