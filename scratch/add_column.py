from database import get_db_connection
from mysql.connector import Error

def add_budget_column():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS monthly_budget DECIMAL(10, 2) DEFAULT 0")
            conn.commit()
            print("Successfully added monthly_budget column.")
        except Error as e:
            if "Duplicate column name" in str(e):
                print("Column already exists.")
            else:
                print(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    add_budget_column()
