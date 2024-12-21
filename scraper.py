import logging
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Configuração do ChromeDriverManager para instalar apenas uma vez
CHROME_DRIVER_PATH = None

# Configuração de logging para rastrear eventos importantes
logging.basicConfig(level=logging.INFO)

def get_driver():
    global CHROME_DRIVER_PATH
    if not CHROME_DRIVER_PATH:
        CHROME_DRIVER_PATH = ChromeDriverManager().install()

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)

def scrape_price(url):
    try:
        logging.info(f"Iniciando raspagem para URL: {url}")
        
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)
        driver.get(url)

        # Aguarda até que o elemento esteja presente
        try:
            product_title = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "productTitle"))
            )
            name = product_title.text.strip()
        except TimeoutException:
            logging.error("Elemento 'productTitle' não encontrado no tempo limite.")
            driver.quit()
            return None, None

        # Recupera o preço
        try:
            price_whole = driver.find_element(By.CSS_SELECTOR, "span.a-price-whole").text
            price_fraction = driver.find_element(By.CSS_SELECTOR, "span.a-price-fraction").text
            price = float(f"{price_whole}.{price_fraction}".replace(",", ""))
        except NoSuchElementException:
            logging.error("Elemento de preço não encontrado.")
            driver.quit()
            return name, None

        driver.quit()
        return name, price

    except Exception as e:
        logging.error(f"Erro ao processar a URL: {url} | Erro: {e}")
        return None, None
