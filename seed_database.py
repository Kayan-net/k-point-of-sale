
import sqlite3

def seed_data():
    """
    Inserts sample data into the 'products' table.
    """
    try:
        conn = sqlite3.connect('pos_system.db')
        cursor = conn.cursor()

        # Sample products
        products = [
            ('Laptop', '1234567890123', 999.99, 50),
            ('Mouse', '2345678901234', 25.50, 200),
            ('Keyboard', '3456789012345', 75.00, 150),
            ('Monitor', '4567890123456', 300.00, 75)
        ]

        # Use executemany for efficiency
        cursor.executemany("INSERT INTO products (name, barcode, price, stock_quantity) VALUES (?, ?, ?, ?)", products)

        conn.commit()
        print(f"Successfully inserted {len(products)} sample products.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    seed_data()
