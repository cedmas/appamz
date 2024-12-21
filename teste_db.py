from db import get_db_connection, fetch_products_with_variation

if __name__ == "__main__":
    try:
        # Testa conexão com o banco
        print("Testando conexão com o banco de dados...")
        conn = get_db_connection()
        print("Conexão estabelecida com sucesso.")
        conn.close()

        # Testa a função fetch_products_with_variation
        print("Testando fetch_products_with_variation...")
        products = fetch_products_with_variation()
        print(f"Produtos retornados ({len(products)}):")
        for product in products:
            print(dict(product))  # Converte sqlite3.Row para dicionário para leitura mais fácil

        print("Teste do banco de dados finalizado com sucesso.")
    except Exception as e:
        print(f"Erro ao testar o banco de dados: {e}")
