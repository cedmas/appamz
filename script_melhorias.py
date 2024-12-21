import sqlite3

DB_PATH = "prices.db"

def apply_improvements():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Criar índice
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_id ON price_history (product_id)")
        print("Índice em 'product_id' criado.")

        # Remover registros órfãos
        cursor.execute('''
            DELETE FROM price_history
            WHERE product_id NOT IN (SELECT id FROM products)
        ''')
        print("Registros órfãos removidos de 'price_history'.")

        # Atualizar last_checked onde está vazio
        cursor.execute('''
            UPDATE products
            SET last_checked = CURRENT_TIMESTAMP
            WHERE last_checked IS NULL
        ''')
        print("Coluna 'last_checked' atualizada.")

        conn.commit()
        print("Melhorias aplicadas com sucesso.")

apply_improvements()
