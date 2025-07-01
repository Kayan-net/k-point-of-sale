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

        conn.commit()
        print("Successfully created 'customers' and 'users' tables.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    update_schema()