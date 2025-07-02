import sqlite3

def update_schema():
    """
    Adds tables for customer and user management.
    """
    try:
        conn = sqlite3.connect('pos_system.db')
        cursor = conn.cursor()

        # Create the 'customers' table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT UNIQUE
        )
        """)

        # Create the 'users' table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL -- e.g., Admin, Staff
        )
        """)

        # Create the 'stores' table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            phone TEXT
        )
        ''')

        # Add store_id to users if not present
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [row[1] for row in cursor.fetchall()]
        if 'store_id' not in user_columns:
            cursor.execute('''ALTER TABLE users ADD COLUMN store_id INTEGER REFERENCES stores(id)''')

        # Add store_id to products if not present
        cursor.execute("PRAGMA table_info(products)")
        product_columns = [row[1] for row in cursor.fetchall()]
        if 'store_id' not in product_columns:
            cursor.execute('''ALTER TABLE products ADD COLUMN store_id INTEGER REFERENCES stores(id)''')

        # Add store_id to sales if not present
        cursor.execute("PRAGMA table_info(sales)")
        sales_columns = [row[1] for row in cursor.fetchall()]
        if 'store_id' not in sales_columns:
            cursor.execute('''ALTER TABLE sales ADD COLUMN store_id INTEGER REFERENCES stores(id)''')

        conn.commit()
        print("Successfully created 'customers', 'users', 'stores' tables and updated schema for multi-store support.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    update_schema()