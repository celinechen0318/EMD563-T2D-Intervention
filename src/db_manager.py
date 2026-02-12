import sqlite3
import os
import pandas as pd

# Path to the database file
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 't2d_system.db')

def init_db():
    """Initialize the database: Create tables for the Pilot Program."""
    # Ensure the directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. User Table 
    # Stores user profile and ADA targets
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            
            -- New Risk Variables (Requested by Prof)
            bmi REAL,                  -- T2D Precursor
            family_history TEXT,       -- 'Yes' or 'No' (Binary)
            
            -- Core Classification
            health_status TEXT,        -- 'Standard', 'Healthy', 'Complex', 'PoorHealth'
            
            -- Personalized Targets (ADA 2026)
            target_fasting_min INTEGER,  
            target_fasting_max INTEGER,
            target_postmeal_max INTEGER,
            target_bp_systolic INTEGER,
            target_bp_diastolic INTEGER
        )
    ''')
    
    # 2. Readings Table 
    # Stores daily metrics and context
    c.execute('''
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            -- A. Biometrics
            glucose_level REAL,
            insulin_level REAL,      -- New: Insulin (uIU/mL)
            bp_systolic INTEGER,
            bp_diastolic INTEGER,
            
            -- B. Context
            meal_tag TEXT,           -- e.g., 'Before Breakfast'
            medication_taken TEXT,   -- 'Yes', 'No', 'Missed'
            activity_notes TEXT,     -- 'Sedentary', 'Walking'
            carbs_intake TEXT,       -- 'Normal', 'High'
            
            -- C. Symptoms
            symptoms TEXT,           
            
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at: {DB_PATH}")

def reset_db():
    """For development: Completely reset the database."""
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print("Old database deleted.")
        except PermissionError:
            print("Could not delete DB file. It might be open elsewhere.")
    init_db()

def create_user(profile):
    """Insert a new user into the database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO users (
            name, age, bmi, family_history, health_status, 
            target_fasting_min, target_fasting_max, 
            target_postmeal_max, target_bp_systolic, target_bp_diastolic
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        profile['name'], profile['age'], 
        profile.get('bmi', 24.0),                 # Default if missing
        profile.get('family_history', 'No'),      # Default to No
        profile['health_status'],
        profile['target_fasting_min'], profile['target_fasting_max'], 
        profile['target_postmeal_max'], profile['target_bp_systolic'], 
        profile['target_bp_diastolic']
    ))
    user_id = c.lastrowid
    conn.commit()
    conn.close()
    return user_id

def add_reading_from_dict(reading_data):
    """Insert a single reading record."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO readings (
            user_id, timestamp, glucose_level, insulin_level,
            bp_systolic, bp_diastolic,
            meal_tag, medication_taken, activity_notes, carbs_intake, symptoms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        reading_data['user_id'], reading_data['timestamp'], 
        reading_data['glucose_level'], 
        reading_data.get('insulin_level', 0.0),   # Default if missing
        reading_data['bp_systolic'], reading_data['bp_diastolic'],
        reading_data['meal_tag'], reading_data['medication_taken'], 
        reading_data['activity_notes'], reading_data['carbs_intake'], reading_data['symptoms']
    ))
    conn.commit()
    conn.close()

def get_recent_readings(user_id, limit=50):
    """Fetch recent readings for the dashboard."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        f"SELECT * FROM readings WHERE user_id={user_id} ORDER BY timestamp DESC LIMIT {limit}",
        conn
    )
    conn.close()
    return df

if __name__ == "__main__":
    reset_db()