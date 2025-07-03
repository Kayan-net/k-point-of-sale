import sqlite3

def update_schema():
    """
    Adds the 'day_log' table for tracking start and end of business days.
    """
    try:
        conn = sqlite3.connect('pos_system.db')
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS day_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            start_time TEXT,
            end_time TEXT,
            user TEXT
        )
        ''')
        conn.commit()
        print("Successfully created 'day_log' table.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    update_schema() 