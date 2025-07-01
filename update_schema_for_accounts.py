import sqlite3

def update_schema():
    """
    Adds tables for the 'accounts' module: chart_of_accounts and journal_entries.
    Also adds categories table and category_id to products for stock categories.
    """
    try:
        conn = sqlite3.connect('pos_system.db')
        cursor = conn.cursor()

        # Create the 'chart_of_accounts' table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chart_of_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_name TEXT NOT NULL UNIQUE,
            account_type TEXT NOT NULL, -- e.g., Asset, Liability, Equity, Revenue, Expense
            initial_balance REAL DEFAULT 0.0
        )
        """)

        # Create the 'journal_entries' table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT,
            total_amount REAL NOT NULL
        )
        """)

        # Create the 'journal_entry_items' table (for debits and credits)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS journal_entry_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            journal_entry_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            debit REAL DEFAULT 0.0,
            credit REAL DEFAULT 0.0,
            FOREIGN KEY (journal_entry_id) REFERENCES journal_entries (id),
            FOREIGN KEY (account_id) REFERENCES chart_of_accounts (id)
        )
        """)

        # Add categories table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
        """)

        # Add category_id to products if not present
        cursor.execute("PRAGMA table_info(products)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'category_id' not in columns:
            cursor.execute("ALTER TABLE products ADD COLUMN category_id INTEGER REFERENCES categories(id)")

        conn.commit()
        print("Successfully created 'chart_of_accounts', 'journal_entries', and 'journal_entry_items' tables.")
        print("Successfully created/updated 'categories' table and 'category_id' in products.")

        ensure_default_accounts(conn)

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

def ensure_default_accounts(conn):
    cursor = conn.cursor()
    default_accounts = [
        ("Cash", "Asset", 0.0),
        ("Accounts Receivable", "Asset", 0.0),
        ("Inventory", "Asset", 0.0),
        ("Sales Revenue", "Revenue", 0.0),
        ("Cost of Goods Sold", "Expense", 0.0),
        ("Accounts Payable", "Liability", 0.0),
        ("Owner's Equity", "Equity", 0.0)
    ]

    for name, acc_type, initial_balance in default_accounts:
        try:
            cursor.execute("INSERT INTO chart_of_accounts (account_name, account_type, initial_balance) VALUES (?, ?, ?)", (name, acc_type, initial_balance))
            print(f"Added default account: {name}")
        except sqlite3.IntegrityError:
            print(f"Default account already exists: {name}")
        except sqlite3.Error as e:
            print(f"Error adding default account {name}: {e}")
    conn.commit()

if __name__ == '__main__':
    update_schema()