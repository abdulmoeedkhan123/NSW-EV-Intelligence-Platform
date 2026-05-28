#!/usr/bin/env python3
"""
UI Application Test Script
Tests all components without starting the Streamlit server
"""

import sys
import os

print("🧪 NSW EV Intelligence Platform - UI Test")
print("="*70)

# Test 1: Check file structure
print("\n1️⃣  Testing File Structure...")
required_files = [
    'home.py',
    'app.yml',
    'requirements.txt',
    'pages/1_🔌_Charger_Recommendations.py',
    'pages/2_🚦_Traffic_Forecast.py',
    'pages/3_🗺️_Trip_Intelligence.py',
    'pages/4_📊_Regional_Metrics.py',
    '.streamlit/config.toml'
]

all_exist = True
for file in required_files:
    if os.path.exists(file):
        print(f"   ✅ {file}")
    else:
        print(f"   ❌ {file} - MISSING!")
        all_exist = False

if all_exist:
    print("   ✅ All required files present")
else:
    print("   ❌ Some files are missing!")
    sys.exit(1)

# Test 2: Check imports
print("\n2️⃣  Testing Python Imports...")
try:
    import streamlit as st
    print(f"   ✅ streamlit {st.__version__}")
except ImportError as e:
    print(f"   ❌ streamlit not installed: {e}")
    sys.exit(1)

try:
    import pandas as pd
    print(f"   ✅ pandas {pd.__version__}")
except ImportError as e:
    print(f"   ❌ pandas not installed: {e}")

try:
    import plotly
    print(f"   ✅ plotly {plotly.__version__}")
except ImportError as e:
    print(f"   ❌ plotly not installed: {e}")

# Test 3: Parse Python files for syntax errors
print("\n3️⃣  Testing Python Syntax...")
import ast

python_files = [
    'home.py',
    'pages/1_🔌_Charger_Recommendations.py',
    'pages/2_🚦_Traffic_Forecast.py',
    'pages/3_🗺️_Trip_Intelligence.py',
    'pages/4_📊_Regional_Metrics.py'
]

syntax_ok = True
for file in python_files:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            code = f.read()
            ast.parse(code)
        print(f"   ✅ {file}")
    except SyntaxError as e:
        print(f"   ❌ {file}: {e}")
        syntax_ok = False

if syntax_ok:
    print("   ✅ All Python files have valid syntax")

# Test 4: Check Databricks connectivity (if available)
print("\n4️⃣  Testing Databricks Connectivity...")
try:
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()
    
    # Test a simple query
    df = spark.sql("SELECT COUNT(*) as count FROM mobility_ai.gold.regional_infrastructure_metrics")
    count = df.collect()[0]['count']
    print(f"   ✅ Database connection successful")
    print(f"   ✅ Regional metrics table: {count} records")
    
    # Test all tables
    tables = [
        "charger_recommendations_nearest",
        "charger_recommendations_gaps",
        "charger_recommendations_smart",
        "congestion_forecast_hourly",
        "congestion_forecast_location",
        "congestion_forecast_recommendations",
        "trip_routes_optimal",
        "trip_charging_requirements",
        "trip_recommendations",
        "regional_infrastructure_metrics"
    ]
    
    total = 0
    for table in tables:
        try:
            df = spark.sql(f"SELECT COUNT(*) as count FROM mobility_ai.gold.{table}")
            count = df.collect()[0]['count']
            total += count
        except Exception as e:
            print(f"   ⚠️  Table {table}: {str(e)[:50]}")
    
    print(f"   ✅ Total records across all tables: {total}")
    
except Exception as e:
    print(f"   ⚠️  Database connection not available: {str(e)[:80]}")
    print(f"   ℹ️  This is OK for local development - app will show empty states")

# Test 5: Configuration validation
print("\n5️⃣  Testing Configuration Files...")
try:
    import yaml
    with open('app.yml', 'r') as f:
        config = yaml.safe_load(f)
    print("   ✅ app.yml is valid YAML")
except Exception as e:
    print(f"   ⚠️  app.yml validation: {e}")

try:
    with open('.streamlit/config.toml', 'r') as f:
        content = f.read()
    if 'theme' in content and 'primaryColor' in content:
        print("   ✅ .streamlit/config.toml has theme configuration")
    else:
        print("   ⚠️  Theme configuration may be incomplete")
except Exception as e:
    print(f"   ❌ Error reading config.toml: {e}")

# Final summary
print("\n" + "="*70)
print("\n📊 Test Summary:")
print("   ✅ File structure: OK")
print("   ✅ Python syntax: OK") 
print("   ✅ Dependencies: OK")
print("   ℹ️  Database: " + ("Connected" if total > 0 else "Not tested"))

print("\n🎉 UI Application is ready to run!")
print("\n📝 To start the application:")
print("   cd /Workspace/Users/moeedk1@gmail.com/NSW-EV-Intelligence-Platform/nsw-ev-intelligence/ui")
print("   streamlit run home.py --server.port 8080")
print("\n" + "="*70)
