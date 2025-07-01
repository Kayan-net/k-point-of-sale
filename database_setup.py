
import sqlite3

def setup_database():
    """
    Creates the SQLite database and the necessary tables if they don't exist.
    """
    try:
        # Connect to the SQLite database (or create it if it doesn't exist)
        conn = sqlite3.connect('pos_system.db')
        cursor = conn.cursor()

        # Create the 'products' table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            barcode TEXT UNIQUE,
            price REAL NOT NULL,
            stock_quantity INTEGER NOT NULL
        )
        """)

        # Commit the changes and close the connection
        conn.commit()
        print("Database and 'products' table created successfully.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    setup_database()
