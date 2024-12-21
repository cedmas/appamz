import sqlite3
import time
import logging
from utils import get_current_time

DB_PATH = "prices.db"

def init_db():
    start_db_time = time.time()  # Marca o início da inicialização do banco de dados
    conn = sqlite3.connect('prices.db')
    cursor = conn.cursor()

    # Cria a tabela de produtos, se não existir
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            price REAL,
            last_checked TIMESTAMP
        )
    ''')

    # Cria a tabela de histórico de preços, se não existir
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            price REAL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')

    conn.commit()
    conn.close()
    logging.info(f"Tempo para inicializar o banco de dados: {time.time() - start_db_time:.2f} segundos")

def get_db_connection():
    """Retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permite acessar as colunas pelo nome
    return conn

def fetch_products_with_variation():
    """Busca todos os produtos com suas respectivas variações de preço."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = '''
        SELECT
            p.id, p.name, p.url, p.price, p.last_checked,
            COALESCE(
                ROUND(((p.price - MAX(ph.price)) / MAX(ph.price)) * 100, 2), 
                0
            ) AS price_variation
        FROM products p
        LEFT JOIN price_history ph ON p.id = ph.product_id
        GROUP BY p.id
    '''
    cursor.execute(query)
    products = cursor.fetchall()
    conn.close()
    return products

def update_prices(product_id, new_price):
    """Atualiza o preço de um produto e registra no histórico, evitando registros repetidos."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Atualiza o preço no produto
        cursor.execute('''
            UPDATE products
            SET price = ?, last_checked = ?
            WHERE id = ?
        ''', (new_price, get_current_time(), product_id))

        # Verifica o último preço registrado no histórico
        cursor.execute('''
            SELECT price 
            FROM price_history
            WHERE product_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
        ''', (product_id,))
        last_price = cursor.fetchone()

        # Insere no histórico apenas se o preço for diferente do último registrado
        if not last_price or last_price[0] != new_price:
            cursor.execute('''
                INSERT INTO price_history (product_id, price)
                VALUES (?, ?)
            ''', (product_id, new_price))

        conn.commit()
    except sqlite3.Error as e:
        print(f"Erro ao atualizar preços: {e}")
    finally:
        conn.close()

def get_all_products():
    """Retorna todos os produtos com informações detalhadas."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = '''
        SELECT 
            id, name, url, price, last_checked,
            ROUND(
                ((price - (
                    SELECT MAX(price)
                    FROM price_history ph
                    WHERE ph.product_id = products.id
                )) / price) * 100, 2
            ) AS price_variation
        FROM products
    '''
    cursor.execute(query)
    products = cursor.fetchall()
    conn.close()
    return products
