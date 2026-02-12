import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os
import db_manager  

# === ADA 2026 GUIDELINES CONFIGURATION ===
ADA_TARGETS = {
    # 1. <65  Standard
    "Standard": {
        "glucose_fasting": (80, 130),
        "glucose_postmeal": (80, 180),
        "bp_target": (110, 130),
        "bp_dia_target": (70, 80),
        "hypo_limit": 70
    },
    # 2. >=65, Healthy
    "Healthy": {
        "glucose_fasting": (80, 130),
        "glucose_postmeal": (80, 180),
        "bp_target": (120, 130),
        "bp_dia_target": (70, 80),
        "hypo_limit": 70
    },
    # 3. >=65, Complex 复杂病史
    "Complex": {
        "glucose_fasting": (90, 150),   
        "glucose_postmeal": (100, 180),
        "bp_target": (130, 140),        
        "bp_dia_target": (75, 90),
        "hypo_limit": 90                
    },
    # 4. >=65, Poor Health
    "PoorHealth": {
        "glucose_fasting": (100, 180),
        "glucose_postmeal": (110, 200),
        "bp_target": (130, 140),
        "bp_dia_target": (80, 90),
        "hypo_limit": 100
    }
}

def generate_user_profile(age=None):
    # random age 40-90
    if age is None:
        age = random.randint(40, 90)
    
    # make sure health condition
    if age < 65:
        status = "Standard"
    else:
        status = random.choice(["Healthy", "Complex", "PoorHealth"])
        
    targets = ADA_TARGETS[status]

    # Precursor
    base_bmi = random.uniform(18.5, 32.0)
    if status in ["Complex", "PoorHealth"]:
        base_bmi += random.uniform(0, 5.0) 
    
    # Binary
    # Mock：70% family history
    fam_history = random.choices(["Yes", "No"], weights=[0.7, 0.3])[0]
    
    return {
        "name": f"Patient_{random.randint(1000, 9999)}",
        "age": age,
        "health_status": status,
        "bmi": round(base_bmi, 1),           
        "family_history": fam_history,       
        "target_fasting_min": targets["glucose_fasting"][0],
        "target_fasting_max": targets["glucose_fasting"][1],
        "target_postmeal_max": targets["glucose_postmeal"][1],
        "target_bp_systolic": targets["bp_target"][1],
        "target_bp_diastolic": targets["bp_dia_target"][1]
    }

def generate_history_data(user_id, profile, days=30):
    status = profile['health_status']
    targets = ADA_TARGETS[status]
    user_bmi = profile['bmi']
    
    data_list = []
    base_date = datetime.now() - timedelta(days=days)
    
    print(f"Generating data for User {user_id} ({status}, Age {profile['age']}, BMI {user_bmi})...")
    
    for day in range(days):
        current_date_base = base_date + timedelta(days=day)
        
        time_slots = [
            ("Before Breakfast", 8), 
            ("2h After Lunch", 14), 
            ("Bedtime", 22)
        ]
        
        for tag, hour in time_slots:
            timestamp = current_date_base.replace(hour=hour, minute=random.randint(0, 59))
            
            # 1. Base Biometrics
            if tag == "Before Breakfast":
                gl_range = targets["glucose_fasting"]
            else:
                gl_range = targets["glucose_postmeal"]
                
            base_glucose = random.randint(gl_range[0], gl_range[1])
            base_bp_sys = random.randint(targets["bp_target"][0] - 10, targets["bp_target"][1])
            base_bp_dia = random.randint(targets["bp_dia_target"][0], targets["bp_dia_target"][1])
            
            # 2. Scenario Injection
            scenario = random.choices(
                ["Normal", "Forgot Meds", "High Carbs", "Exercise", "Hypo Risk"],
                weights=[0.70, 0.05, 0.15, 0.05, 0.05]
            )[0]
            
            meds = "Yes"
            activity = "Sedentary"
            carbs = "Normal"
            symptoms = "None"
            
            if scenario == "Forgot Meds":
                meds = "No"
                base_glucose += random.randint(40, 70)  
                
            elif scenario == "High Carbs" and tag != "Before Breakfast":
                carbs = "High"
                base_glucose += random.randint(50, 90) 
                
            elif scenario == "Exercise":
                activity = "Walking"
                base_glucose -= random.randint(15, 30)  
                
            elif scenario == "Hypo Risk":
                base_glucose = random.randint(50, targets["hypo_limit"] - 5)
                symptoms = "Dizzy"

            # Insulin
            # baseline: 5-15 uIU/mL
            base_insulin = random.uniform(5, 12)
            
            if user_bmi > 25.0:
                base_insulin += random.uniform(5, 15) 
            
            if base_glucose > 180:
                base_insulin += random.uniform(10, 20) 
            
            
            row = {
                "user_id": user_id,
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "glucose_level": base_glucose,
                "insulin_level": round(base_insulin, 1), 
                "bp_systolic": base_bp_sys,
                "bp_diastolic": base_bp_dia,
                "meal_tag": tag,
                "medication_taken": meds,
                "activity_notes": activity,
                "carbs_intake": carbs,
                "symptoms": symptoms
            }
            

            try:
                db_manager.add_reading_from_dict(row)
            except Exception as e:
                print(f"⚠️ Warning: Database insert failed (Columns missing?). Saving to CSV only. Error: {e}")
            
            data_list.append(row)
            
    print(f"Generated {len(data_list)} records for User {user_id}.")
    return pd.DataFrame(data_list)

if __name__ == "__main__":
    db_manager.reset_db()

    profile = generate_user_profile(age=68) 
    user_id = db_manager.create_user(profile)
    print(f"Created User: {profile['name']} | Status: {profile['health_status']} | BMI: {profile['bmi']} | Family Hist: {profile['family_history']}")

    df = generate_history_data(user_id, profile, days=30)
    
    save_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        
    save_path = os.path.join(save_dir, 'simulation_data.csv')
    df.to_csv(save_path, index=False)
    print(f"Backup CSV saved to: {save_path}")