import sqlite3

def check_table_structure():
    conn = sqlite3.connect('prices.db')  # Conecta ao banco de dados
    cursor = conn.cursor()

    # Mostra a estrutura da tabela 'products'
    print("\nEstrutura da tabela 'products':")
    cursor.execute("PRAGMA table_info(products)")
    for column in cursor.fetchall():
        print(column)

    # Mostra os dados atuais da tabela 'products'
    print("\nDados da tabela 'products':")
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    for row in rows:
        print(row)

    # Mostra os dados da tabela 'price_history'
    print("\nEstrutura da tabela 'price_history':")
    cursor.execute("PRAGMA table_info(price_history)")
    for column in cursor.fetchall():
        print(column)

    print("\nDados da tabela 'price_history':")
    cursor.execute("SELECT * FROM price_history")
    rows = cursor.fetchall()
    for row in rows:
        print(row)

    conn.close()

if __name__ == "__main__":
    check_table_structure()
