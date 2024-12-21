import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler

# Inicializa o Flask
app = Flask(__name__)

# Configuracao de Cache para evitar requisicoes duplicadas
cache = {}

# Inicializa o banco de dados
def init_db():
    conn = sqlite3.connect('prices.db')
    cursor = conn.cursor()
    
    # Tabela de produtos
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        url TEXT,
                        price REAL
                    )''')
    
    # Tabela de historico de precos
    cursor.execute('''CREATE TABLE IF NOT EXISTS price_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER,
                        price REAL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(product_id) REFERENCES products(id)
                    )''')
    conn.commit()
    conn.close()

# Funcao para obter o preco via scraping com timeout e cache
def scrape_price(url):
    try:
        print(f"URL recebida: {url}")

        # Configuração do cabeçalho para imitar um navegador real
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # Faz a requisição HTTP
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()  # Gera erro se a resposta for ruim (ex: 404)
        print("Resposta obtida com sucesso.")

        # Salva o HTML em um arquivo local para inspeção
        with open("debug_page.html", "w", encoding="utf-8") as file:
            file.write(response.text)
        print("HTML salvo em 'debug_page.html'. Abra este arquivo no navegador para inspecionar.")

        # Parseia o HTML com BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # **Extrai o nome do produto**
        product_name_tag = soup.find("span", {"id": "productTitle"})
        product_name = product_name_tag.text.strip() if product_name_tag else "Produto Sem Nome"

        # **Extrai o preço do produto**
        price_whole = soup.select_one("span.a-price-whole")  # Parte inteira
        price_fraction = soup.select_one("span.a-price-fraction")  # Parte decimal

        # Se preço padrão não for encontrado, tenta no 'a-offscreen' (preço alternativo)
        if price_whole and price_fraction:
            price = f"{price_whole.text.strip()}.{price_fraction.text.strip()}"
            price_float = float(price.replace(",", "").strip())
        else:
            price_tag = soup.find("span", {"class": "a-offscreen"})
            if price_tag:
                price_float = float(price_tag.text.strip().replace("R$", "").replace(",", "."))
            else:
                print("Preço não encontrado.")
                return product_name, None

        print(f"Produto: {product_name}")
        print(f"Preço: R$ {price_float:.2f}")
        return product_name, price_float

    except requests.Timeout:
        print("Erro: Tempo limite atingido ao acessar a URL.")
        return None, None
    except Exception as e:
        print(f"Erro ao processar a página: {e}")
        return None, None

# Testando com URLs fornecidas
if __name__ == "__main__":
    urls = [
        "https://www.amazon.com.br/Vinho-Branco-Sweet-Casal-Garcia/dp/B08DPLVQRZ",
        "https://www.amazon.com.br/PlayStation-DualSense-Controle-sem-fio/dp/B0CQKLS4RP",
        "https://www.amazon.com.br/Whisky-Escoc%C3%AAs-Black-Label-Garrafa/dp/B00861CC7Y",
        "https://www.amazon.com.br/Whisky-Buchanans-Deluxe-anos-750ml/dp/B001QZ5GUW"
    ]

    for url in urls:
        print("\n--- Testando URL ---")
        name, price = scrape_price(url)
        if price:
            print(f"✅ Nome: {name} | Preço: R$ {price:.2f}")
        else:
            print(f"❌ Não foi possível obter o preço do produto: {name}")

# Rotas do Flask
@app.route('/')
def index():
    conn = sqlite3.connect('prices.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return render_template('index.html', products=products)

@app.route('/add', methods=['POST'])
def add_product():
    url = request.form['url']
    print(f"Adicionando produto, URL: {url}")
    
    # Obtém o nome e o preço do produto automaticamente
    product_name, price = scrape_price(url)

    if product_name and price:
        conn = sqlite3.connect('prices.db')
        cursor = conn.cursor()
        
        # Insere o produto na tabela products
        cursor.execute("INSERT INTO products (name, url, price) VALUES (?, ?, ?)", (product_name, url, price))
        product_id = cursor.lastrowid
        
        # Insere o preço no histórico
        cursor.execute("INSERT INTO price_history (product_id, price) VALUES (?, ?)", (product_id, price))
        conn.commit()
        conn.close()
        print(f"Produto '{product_name}' adicionado com sucesso. Preço: R$ {price:.2f}")
    else:
        print("Não foi possível obter o nome ou o preço do produto.")

    return redirect(url_for('index'))

@app.route('/delete/<int:product_id>')
def delete_product(product_id):
    conn = sqlite3.connect('prices.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    cursor.execute("DELETE FROM price_history WHERE product_id = ?", (product_id,))
    conn.commit()
    conn.close()
    print(f"Produto com ID {product_id} removido.")
    return redirect(url_for('index'))

@app.route('/history/<int:product_id>')
def price_history(product_id):
    conn = sqlite3.connect('prices.db')
    cursor = conn.cursor()
    
    # Busca o nome do produto
    cursor.execute("SELECT name FROM products WHERE id = ?", (product_id,))
    product_name = cursor.fetchone()
    product_name = product_name[0] if product_name else "Produto Desconhecido"
    
    # Busca o historico de precos
    cursor.execute("SELECT price, updated_at FROM price_history WHERE product_id = ? ORDER BY updated_at DESC", (product_id,))
    history = cursor.fetchall()
    conn.close()
    return render_template('history.html', history=history, product_id=product_id, product_name=product_name)

# Tarefa agendada para atualizar os precos periodicamente
def update_prices():
    conn = sqlite3.connect('prices.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, url, price FROM products")
    products = cursor.fetchall()
    
    for product_id, url, old_price in products:
        new_price = scrape_price(url)
        
        if new_price:
            # Compara o preco atual com o anterior
            if new_price != old_price:
                if new_price < old_price:
                    print(f"\ud83d\udd3b Preco do produto ID {product_id} caiu para R$ {new_price:.2f} (Antes: R$ {old_price:.2f})")
                elif new_price > old_price:
                    print(f"\ud83d\udd3a Preco do produto ID {product_id} subiu para R$ {new_price:.2f} (Antes: R$ {old_price:.2f})")
                
                # Atualiza o preco na tabela de produtos
                cursor.execute("UPDATE products SET price = ? WHERE id = ?", (new_price, product_id))
                
                # Salva o preco no historico
                cursor.execute("INSERT INTO price_history (product_id, price) VALUES (?, ?)", (product_id, new_price))
    
    conn.commit()
    conn.close()

# Inicializa o agendador
scheduler = BackgroundScheduler()
scheduler.add_job(update_prices, "interval", hours=1)  # Atualiza a cada 1 hora
scheduler.start()

# Inicializa o banco de dados
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
