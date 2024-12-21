import requests
from bs4 import BeautifulSoup

# Função para buscar o preço e o nome do produto
def scrape_price(url):
    try:
        print(f"URL recebida: {url}")

        # Configuração do cabeçalho para imitar um navegador real
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # Faz a requisição HTTP para obter o conteúdo da página
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        print("Resposta obtida com sucesso.")

        # Salva o HTML em um arquivo local para depuração (caso algo falhe)
        with open("debug_page.html", "w", encoding="utf-8") as file:
            file.write(response.text)
        print("HTML salvo em 'debug_page.html' para inspeção.")

        # Parseia o HTML da página
        soup = BeautifulSoup(response.content, "html.parser")

        # **Extrai o nome do produto** (usando o ID padrão 'productTitle')
        product_name_tag = soup.find("span", {"id": "productTitle"})
        product_name = product_name_tag.text.strip() if product_name_tag else "Produto Sem Nome"

        # **Extrai o preço do produto** (tentando múltiplas tags)
        price_whole = soup.select_one("span.a-price-whole")
        price_fraction = soup.select_one("span.a-price-fraction")

        # Fallback: tenta o 'a-offscreen' para preços alternativos
        price_tag = soup.find("span", {"class": "a-offscreen"})

        # Combina as partes do preço, se disponível
        if price_whole and price_fraction:
            price = f"{price_whole.text.strip()}.{price_fraction.text.strip()}"
            price_float = float(price.replace(",", "").strip())
        elif price_tag:
            price_float = float(price_tag.text.strip().replace("R$", "").replace(",", "."))
        else:
            print("Preço não encontrado.")
            return product_name, None

        # Log do resultado no terminal
        print(f"Produto: {product_name}")
        print(f"Preço: R$ {price_float:.2f}")
        return product_name, price_float

    # Tratamento de erros
    except requests.exceptions.Timeout:
        print("Erro: Tempo limite atingido ao fazer a requisição.")
        return None, None
    except Exception as e:
        print(f"Erro ao processar a página: {e}")
        return None, None

# Testando a função com URLs da Amazon
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
