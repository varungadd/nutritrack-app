import sqlite3
import os

DB_PATH = 'health.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Create foods table
    c.execute('''
        CREATE TABLE IF NOT EXISTS foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            calories INTEGER NOT NULL,
            protein REAL NOT NULL,
            carbs REAL NOT NULL,
            fat REAL NOT NULL
        )
    ''')
    
    # Create meal_logs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS meal_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            food_id INTEGER NOT NULL,
            servings REAL NOT NULL,
            meal_type TEXT NOT NULL,
            FOREIGN KEY (food_id) REFERENCES foods (id)
        )
    ''')

    # Create water_logs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS water_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            glasses INTEGER NOT NULL DEFAULT 0
        )
    ''')

    # Create user_profile table
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            height_cm REAL DEFAULT 170,
            weight_kg REAL DEFAULT 70,
            calorie_goal INTEGER DEFAULT 2000,
            protein_goal INTEGER DEFAULT 150,
            carbs_goal INTEGER DEFAULT 200,
            fat_goal INTEGER DEFAULT 65,
            last_login_date TEXT,
            streak_count INTEGER DEFAULT 0
        )
    ''')

    # Add indexes for efficiency
    c.execute('CREATE INDEX IF NOT EXISTS idx_foods_name ON foods(name COLLATE NOCASE)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_meal_logs_date ON meal_logs(date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_water_logs_date ON water_logs(date)')

    # Initialize user profile if empty
    c.execute('SELECT COUNT(*) FROM user_profile')
    if c.fetchone()[0] == 0:
        c.execute('''
            INSERT INTO user_profile (height_cm, weight_kg, calorie_goal) 
            VALUES (175, 70, 2000)
        ''')

    # Check if foods table is empty, if so, populate with mock data
    c.execute('SELECT COUNT(*) FROM foods')
    if c.fetchone()[0] == 0:
        mock_foods = [
            ('Apple (1 medium)', 95, 0.5, 25, 0.3),
            ('Banana (1 medium)', 105, 1.3, 27, 0.3),
            ('Chicken Breast (100g)', 165, 31, 0, 3.6),
            ('Brown Rice (1 cup)', 216, 5, 45, 1.8),
            ('Broccoli (1 cup)', 55, 3.7, 11, 0.6),
            ('Salmon (100g)', 208, 20, 0, 13),
            ('Egg (Large)', 78, 6.3, 0.6, 5.3),
            ('Oatmeal (1 cup)', 158, 6, 27, 3.2),
            ('Almonds (1 oz)', 164, 6, 6, 14),
            ('Greek Yogurt (1 cup)', 100, 10, 4, 0),
            ('Avocado (1 medium)', 234, 2.9, 12, 21),
            ('Spinach (1 cup raw)', 7, 0.9, 1.1, 0.1),
            ('Sweet Potato (1 medium)', 103, 2, 24, 0.2),
            ('Quinoa (1 cup cooked)', 222, 8.1, 39, 3.6),
            ('Peanut Butter (2 tbsp)', 188, 8, 6, 16),
            # Indian Foods
            ('Dal Tadka (1 cup)', 208, 11, 31, 5),
            ('Paneer Butter Masala (1 cup)', 380, 14, 18, 28),
            ('Roti (1 piece)', 104, 3, 22, 0.4),
            ('Plain Rice (1 cup)', 205, 4.3, 45, 0.4),
            ('Samosa (1 piece)', 260, 3.5, 32, 13),
            ('Chana Masala (1 cup)', 268, 12, 40, 7),
            ('Idli (1 piece)', 39, 1.2, 8, 0.1),
            ('Plain Dosa (1 piece)', 133, 2.7, 23, 3),
            ('Masala Dosa (1 piece)', 415, 8, 61, 16),
            ('Palak Paneer (1 cup)', 290, 13, 10, 23),
            ('Aloo Gobi (1 cup)', 140, 4, 20, 5),
            ('Butter Chicken (1 cup)', 420, 25, 15, 28),
            ('Naan (1 piece)', 260, 8, 43, 6),
            ('Garlic Naan (1 piece)', 285, 8, 45, 8),
            ('Poha (1 cup)', 180, 4, 32, 4),
            ('Upma (1 cup)', 210, 5, 35, 6),
            ('Rajma (1 cup)', 260, 14, 45, 3),
            ('Gulab Jamun (1 piece)', 150, 2, 25, 5),
            ('Biryani (Chicken, 1 cup)', 360, 18, 45, 12),
            ('Vegetable Biryani (1 cup)', 250, 6, 45, 6)
        ]
        c.executemany('''
            INSERT INTO foods (name, calories, protein, carbs, fat)
            VALUES (?, ?, ?, ?, ?)
        ''', mock_foods)
        
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized.")
