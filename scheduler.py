import logging
import time
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
from db import get_db_connection, update_prices
from scraper import scrape_price

logging.basicConfig(level=logging.INFO)
scheduler = None  # Variável global para o agendador

def update_all_prices():
    """
    Atualiza os preços de todos os produtos na tabela 'products'.
    Registra as alterações no histórico de preços e loga o status.
    """
    try:
        start_update_time = time.time()  # Marca o início da atualização
        with get_db_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, url, name FROM products")
            products = cursor.fetchall()

            for product in products:
                product_id = product['id']
                product_name = product['name']
                url = product['url']

                # Raspagem de preço
                scraped_name, new_price = scrape_price(url)
                if new_price is not None:
                    update_prices(product_id, new_price)
                    logging.info(f"🔄 Preço atualizado para {product_name}: R$ {new_price:.2f}")
                else:
                    logging.warning(f"⚠️ Não foi possível atualizar o preço de {product_name}.")
        
        # Loga o tempo total da atualização
        logging.info(f"Tempo para atualizar todos os preços: {time.time() - start_update_time:.2f} segundos")
    
    except Exception as e:
        logging.error(f"Erro ao atualizar os preços: {e}")

def start_scheduler(interval_minutes=5):
    """
    Inicializa o agendador para executar atualizações periódicas de preços.
    """
    global scheduler
    if scheduler is not None:
        logging.warning("Agendador já iniciado.")
        return

    try:
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            update_all_prices,
            trigger="interval",
            minutes=interval_minutes,
            max_instances=1,
            misfire_grace_time=30
        )
        scheduler.start()
        logging.info(f"✅ Agendador iniciado com intervalo de {interval_minutes} minutos.")
    except Exception as e:
        logging.error(f"Erro ao iniciar o agendador: {e}")

def update_scheduler_interval(new_interval):
    """
    Atualiza o intervalo de execução do job de atualização.
    """
    global scheduler
    if scheduler is None:
        logging.error("Scheduler não inicializado.")
        return

    try:
        # Remove todos os jobs existentes
        for job in scheduler.get_jobs():
            scheduler.remove_job(job.id)

        # Adiciona um novo job com o intervalo atualizado
        scheduler.add_job(
            update_all_prices,
            trigger="interval",
            minutes=new_interval,
            max_instances=1,
            misfire_grace_time=30
        )
        logging.info(f"Intervalo de atualização alterado para {new_interval} minutos.")
    except Exception as e:
        logging.error(f"Erro ao atualizar o agendador: {e}")
