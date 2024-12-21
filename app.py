import time  # Importação para medir o tempo
from scheduler import update_all_prices
import os
start_time = time.time()  # Marca o início do processo

from flask import Flask, render_template, request, redirect, url_for
from db import init_db, get_db_connection, fetch_products_with_variation, update_prices  # Importação corrigida
from scheduler import start_scheduler, update_scheduler_interval, scheduler
from scraper import scrape_price
import logging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

@app.route('/')
def index():
    products = fetch_products_with_variation()
    return render_template('index.html', products=products)

@app.route('/add', methods=['POST'])
def add_product():
    url = request.form['url']
    name, price = scrape_price(url)

    if name and price:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO products (name, url, price, last_checked)
            VALUES (?, ?, ?, ?)
        ''', (name, url, price, None))
        conn.commit()
        conn.close()

    return redirect(url_for('index'))

@app.route('/delete/<int:product_id>')
def delete_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    cursor.execute("DELETE FROM price_history WHERE product_id = ?", (product_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/update_all', methods=['POST'])
def update_all_prices_endpoint():
    try:
        update_all_prices()
    except Exception as e:
        logging.error(f"Erro ao atualizar todos os preços: {e}")
    return redirect(url_for('index'))

@app.route('/update/<int:product_id>', methods=['POST'])
def update_product(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT url, name FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        if product:
            url, name = product
            scraped_name, new_price = scrape_price(url)
            if new_price:
                update_prices(product_id, new_price)  # Garantia de que a função está importada
                logging.info(f"🔄 Preço atualizado para {name}: R$ {new_price:.2f}")
            else:
                logging.warning(f"⚠️ Não foi possível atualizar o preço de {name}.")
        else:
            logging.error(f"Produto com ID {product_id} não encontrado.")
    except Exception as e:
        logging.error(f"Erro ao atualizar o produto ID {product_id}: {e}")
    finally:
        conn.close()
    return redirect(url_for('index'))

@app.route('/update_interval', methods=['POST'])
def update_interval():
    new_interval = int(request.form['interval'])
    update_scheduler_interval(new_interval)
    return redirect(url_for('index'))

@app.route('/history/<int:product_id>')
def price_history(product_id):
    """
    Exibe o histórico de preços de um produto específico.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Busca o nome do produto
        cursor.execute("SELECT name FROM products WHERE id = ?", (product_id,))
        product_name = cursor.fetchone()
        product_name = product_name[0] if product_name else "Produto Desconhecido"

        # Busca o histórico de preços (inclui ID para exclusão)
        cursor.execute("SELECT price, updated_at, id FROM price_history WHERE product_id = ? ORDER BY updated_at", (product_id,))
        history = cursor.fetchall()

        conn.close()

        # Prepara dados para o gráfico
        labels = [record[1] for record in history] if history else []  # Datas
        prices = [record[0] for record in history] if history else []  # Preços

        return render_template('history.html', history=history, product_name=product_name, labels=labels, prices=prices)
    except Exception as e:
        logging.error(f"Erro ao carregar histórico de preços para o produto ID {product_id}: {e}")
        return "Erro ao carregar histórico de preços.", 500

@app.route('/delete_history', methods=['POST'])
def delete_history():
    """
    Exclui um registro específico do histórico de preços.
    """
    history_id = request.form['history_id']
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM price_history WHERE id = ?", (history_id,))
        conn.commit()
        conn.close()
        logging.info(f"Registro de histórico ID {history_id} excluído com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao excluir registro de histórico ID {history_id}: {e}")
    return redirect(request.referrer or url_for('index'))

if __name__ == '__main__':
    init_db()
    start_scheduler(interval_minutes=5)
    logging.info(f"Tempo total de inicialização: {time.time() - start_time:.2f} segundos")
    port = int(os.environ.get("PORT", 5000))  # Obtém a porta da variável de ambiente ou usa 5000 como padrão
app.run(host="0.0.0.0", port=port, debug=False)
