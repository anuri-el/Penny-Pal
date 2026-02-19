import sqlite3


conn = sqlite3.connect('pennypal.db')


c = conn.cursor()


c.execute("""
          CREATE TABLE users(
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER NOT NULL UNIQUE,
                telegram_username TEXT UNIQUE,
                first_name TEXT,
                last_name TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP)
            """)


c.execute("""
          CREATE TABLE categories(
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            category_name TEXT)
          """)


c.execute("""
          CREATE TABLE transactions(
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            category_id INTEGER REFERENCES categories(id),
            transaction_name TEXT,
            amount REAL,
            type TEXT,
            date_time DATETIME DEFAULT CURRENT_TIMESTAMP)
          """)


c.execute("""
          CREATE TABLE budgets(
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            category_id INTEGER REFERENCES categories(id),
            amount REAL,
            month_year DATETIME DEFAULT CURRENT_TIMESTAMP)
          """)

# c.execute("SELECT * FROM users")
# print(c.fetchall())

conn.commit()


conn.close()
