
import sqlite3

def update_schema():
    """
    Adds tables for managing suppliers and purchase orders.
    """
    try:
        conn = sqlite3.connect('pos_system.db')
        cursor = conn.cursor()

        # Create the 'suppliers' table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            contact_info TEXT
        )
        """)

        # Create the 'purchase_orders' table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_amount REAL NOT NULL,
            FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
        )
        """)

        # Create the 'purchase_order_items' table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            cost_per_unit REAL NOT NULL,
            FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        """)

        conn.commit()
        print("Successfully created 'suppliers' and purchase-related tables.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    update_schema()
