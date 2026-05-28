import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Demo data generator for offline testing
def generate_demo_data():
    """Generate sample data matching the schema of mobility_ai.gold tables"""
    
    # Charger nearest data
    charger_nearest = pd.DataFrame({
        'lganame': np.random.choice(['Sydney', 'Newcastle', 'Wollongong', 'Central Coast'], 100),
        'operator': np.random.choice(['ChargeFox', 'Evie', 'NRMA', 'Tesla'], 100),
        'charging_speed': np.random.choice(['Slow', 'Fast', 'Rapid', 'Ultra Rapid'], 100),
        'charger_rating_kw': np.random.randint(7, 350, 100),
        'distance_km': np.random.uniform(0.5, 20, 100),
        'accessibility_score': np.random.uniform(6, 10, 100),
        'total_plugs': np.random.randint(1, 8, 100)
    })
    
    # Charger gaps data
    charger_gaps = pd.DataFrame({
        'lganame': ['Sydney', 'Newcastle', 'Wollongong', 'Central Coast', 'Blue Mountains'],
        'gap_category': np.random.choice(['Low', 'Medium', 'High'], 5),
        'slow_chargers': np.random.randint(50, 300, 5),
        'fast_chargers': np.random.randint(30, 200, 5),
        'rapid_chargers': np.random.randint(10, 100, 5),
        'total_capacity_kw': np.random.uniform(1000, 5000, 5),
        'gap_severity': np.random.uniform(3, 9, 5)
    })
    
    # Congestion hourly data
    hours = list(range(24))
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    congestion_hourly = []
    for day in days:
        for hour in hours:
            congestion_hourly.append({
                'hour_of_day': hour,
                'day_name': day,
                'congestion_level': 'High' if 7 <= hour <= 9 or 16 <= hour <= 18 else 'Medium' if 10 <= hour <= 15 else 'Low',
                'congestion_score': np.random.uniform(3, 9) if 7 <= hour <= 9 or 16 <= hour <= 18 else np.random.uniform(2, 6),
                'total_hazards': np.random.randint(0, 15),
                'major_hazards': np.random.randint(0, 5),
                'moderate_hazards': np.random.randint(0, 8),
                'minor_hazards': np.random.randint(0, 10),
                'is_peak_hour': 7 <= hour <= 9 or 16 <= hour <= 18
            })
    congestion_hourly = pd.DataFrame(congestion_hourly)
    
    return {
        'charger_nearest': charger_nearest,
        'charger_gaps': charger_gaps,
        'congestion_hourly': congestion_hourly
    }

if __name__ == "__main__":
    st.title("Demo Data Generator")
    st.write("This script generates sample data for testing the UI without database connection")
    
    if st.button("Generate Demo Data"):
        data = generate_demo_data()
        st.success("Demo data generated!")
        
        for name, df in data.items():
            st.subheader(name)
            st.dataframe(df.head())
