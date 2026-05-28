# Databricks Notebooks

Data processing notebooks organized by medallion architecture (Bronze → Silver → Gold).

## 🏗️ Structure

```
notebooks/
├── bronze/              # Raw data ingestion (4 notebooks)
├── silver/              # Data transformation (4 notebooks)
├── gold/                # Analytics & ML (2 notebooks)
└── README.md           # This file
```

## 📊 Data Pipeline Overview

### Total: 10 Notebooks
- **4 Bronze** (Ingestion): 13,036 raw records
- **4 Silver** (Transformation): 13,028 cleaned records
- **2 Gold** (Analytics): 4,139 aggregated insights

---

## 🔵 Bronze Layer (Raw Ingestion)

Fetch data from NSW Government APIs and land in Delta Lake without transformation.

### 1. `ingest_ev_charging_stations.py`
**Purpose**: Ingest EV charging station locations and specifications  
**Source**: NSW EV Charging Stations API  
**Target**: `mobility_ai.bronze.ev_charging_stations_raw`  
**Records**: 1,958 stations  
**Key Fields**: Station name, address, lat/lon, operator, charger rating

### 2. `ingest_traffic_hazards.py`
**Purpose**: Ingest real-time traffic hazards and roadwork  
**Source**: NSW Traffic Hazards API (Live Traffic NSW)  
**Target**: `mobility_ai.bronze.traffic_hazards_raw`  
**Records**: 431 hazards  
**Key Fields**: Hazard type, location, severity, start/end time, headline

### 3. `ingest_fuel_prices.py`
**Purpose**: Ingest fuel prices from petrol stations  
**Source**: NSW Fuel Check API  
**Target**: `mobility_ai.bronze.fuel_raw`  
**Records**: 10,627 price records  
**Key Fields**: Station code, fuel type, price, last updated, brand

### 4. `ingest_weather_conditions.py`
**Purpose**: Ingest weather observations  
**Source**: Weather API  
**Target**: `mobility_ai.bronze.weather_raw`  
**Records**: 20 weather stations  
**Key Fields**: Station, temperature, humidity, precipitation, wind speed

**Common Pattern**:
```python
1. Fetch JSON from API (requests library)
2. Convert to Spark DataFrame
3. Add ingestion_timestamp
4. Write to Delta Lake (append/overwrite)
```

---

## 🔸 Silver Layer (Cleaned & Validated)

Transform bronze data into analysis-ready tables with data quality flags.

### 1. `transform_ev_charging_stations.py`
**Source**: `bronze.ev_charging_stations_raw`  
**Target**: `silver.ev_charging_stations`  
**Records**: 1,950 (8 duplicates removed)

**Transformations**:
- Column standardization (snake_case using regex)
- Charger rating parsing: "50 kW" → 50.0 (numeric)
- Speed categorization: Slow/Fast/Rapid/Ultra-Rapid
- Quality flags: `has_valid_location`, `has_valid_rating`
- Deduplication: Window function on station_name + coordinates

**Key Findings**:
- 27% missing/invalid ratings ("AC" without numeric value)
- 0% missing coordinates (all stations have valid location)
- 51% rapid chargers (22-150 kW)

### 2. `transform_traffic_hazards.py`
**Source**: `bronze.traffic_hazards_raw`  
**Target**: `silver.traffic_hazards`  
**Records**: 429 (2 duplicates removed)

**Transformations**:
- Timestamp parsing: DD/MM/YYYY format → timestamp
- Severity classification: Major/Moderate/Minor
- Active status calculation: Filter by start/end time
- Composite key: headline + lat + lon (100% missing hazard_id)
- Hazard type cleaning and categorization

**Key Findings**:
- 79% roadwork events
- 66% currently active hazards
- 13% missing start_time (immediate incidents)
- 100% missing unique hazard IDs from API

### 3. `transform_fuel_prices.py`
**Source**: `bronze.fuel_raw`  
**Target**: `silver.fuel_prices`  
**Records**: 10,627 (no duplicates)

**Transformations**:
- Fuel categorization: Regular Unleaded, Premium 95/98, Diesel, LPG
- Price validation: 0-500 cents/liter range check
- Timestamp parsing: DD/MM/YYYY HH:mm:ss format
- Quality flags: `has_valid_price`, `has_valid_station`, `has_valid_timestamp`
- Deduplication: By station + fuel type + date

**Key Findings**:
- 8.5% invalid prices (mostly EV charging at $0.00)
- Average prices: Diesel 226.5¢/L, Unleaded 183.9¢/L, LPG 121.5¢/L
- 3,286 unique fuel stations

### 4. `transform_weather_conditions.py`
**Source**: `bronze.weather_raw`  
**Target**: `silver.weather_conditions`  
**Records**: 20 (no duplicates)

**Transformations**:
- Weather categorization: Clear, Cloudy, Rain, Storm, Snow/Ice, Fog, Windy
- NSW boundary validation: Lat (-37.5 to -28.0), Lon (140.0 to 154.0)
- Metric validations: Temp (-50 to 60°C), Humidity (0-100%)
- Quality flags: 7 different validation flags
- Deduplication: By station_id + timestamp

**Key Findings**:
- All 20 stations have valid data
- Full NSW coverage with observation stations

---

## 🟡 Gold Layer (Business Intelligence)

Business-ready analytics, aggregations, and ML features.

### 1. `regional_infrastructure_metrics.py`
**Sources**: `silver.ev_charging_stations`, `silver.fuel_prices`  
**Target**: `gold.regional_infrastructure_metrics`  
**Records**: 9 NSW regions

**Purpose**: Regional EV infrastructure readiness analysis

**Analytics**:
- **8 NSW Regions** + "Other" catchall
- **EV Readiness Score** (0-100):
  - Station count: 40% weight
  - Fast charger %: 30% weight
  - Total capacity: 30% weight
- **Regional boundaries**: Lat/lon-based segmentation
- **Fuel price benchmarks**: State-wide aggregation (no location data)

**Key Outputs**:
- Sydney Metro: 882 stations, 94/100 score
- Western NSW: 10 stations, 28/100 score (critical gap)
- NSW average: 37.2% EV-to-fuel infrastructure ratio

### 2. `charger_recommendation.py`
**Sources**: `silver.ev_charging_stations`, `silver.traffic_hazards`, `silver.weather_conditions`  
**Targets**: 
- `gold.charger_recommendations_nearest` (80 recs)
- `gold.charger_recommendations_gaps` (150 LGAs)
- `gold.charger_recommendations_smart` (1,950 stations)

**Purpose**: Intelligent charger recommendations with real-time conditions

**Analytics**:

#### a) Nearest Charger Finder
- **Haversine distance** calculation (great-circle)
- **8 reference locations**: Sydney CBD, Newcastle, Wollongong, etc.
- **Top 10 nearest** chargers per location
- Output: Distance (km), speed, operator, address

#### b) Infrastructure Gap Analysis
- **Gap Severity Score** (0-100):
  - Charger count deficit: 40 points
  - Capacity shortfall: 30 points
  - Rapid charger gap: 30 points
- **Categories**: Critical, High, Moderate, Low
- **LGA-level granularity** (150 regions analyzed)

#### c) Smart Recommendations
- **Accessibility Score**: Traffic hazards within 5km radius
- **Recommendation Score** (0-100):
  - Charger quality: 40% (Ultra-Rapid > Rapid > Fast > Slow)
  - Real-time accessibility: 60%
- **Tiers**: Excellent, Good, Fair, Limited
- Considers: 284 active traffic hazards

**Key Outputs**:
- 80 nearest charger recommendations
- 150 LGA gaps identified for infrastructure investment
- 1,950 real-time scored chargers

---

## 🚀 Execution Order

### Full Pipeline (Cold Start)
```bash
# Step 1: Bronze Layer
ingest_ev_charging_stations.py
ingest_traffic_hazards.py
ingest_fuel_prices.py
ingest_weather_conditions.py

# Step 2: Silver Layer
transform_ev_charging_stations.py
transform_traffic_hazards.py
transform_fuel_prices.py
transform_weather_conditions.py

# Step 3: Gold Layer
regional_infrastructure_metrics.py
charger_recommendation.py
```

### Incremental Updates
```bash
# Real-time (hourly)
ingest_traffic_hazards.py
transform_traffic_hazards.py
charger_recommendation.py  # Refresh smart recs

# Daily
ingest_fuel_prices.py
transform_fuel_prices.py

# Weekly
ingest_ev_charging_stations.py
transform_ev_charging_stations.py
regional_infrastructure_metrics.py
```

---

## 🔧 Technical Patterns

### Common Imports
```python
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import DoubleType
import re, math
```

### Column Standardization
```python
# Regex-based snake_case conversion
for col in df.columns:
    new_col = re.sub(r'(?<!^)(?=[A-Z])', '_', col).lower()
    df = df.withColumnRenamed(col, new_col)
```

### Safe Type Casting
```python
# Use try_cast via F.expr() instead of direct cast
F.expr("try_cast(charger_rating as double)")
```

### Data Quality Flags
```python
has_valid_location = (
    (F.col("latitude").isNotNull()) & 
    (F.col("longitude").isNotNull())
)
```

### Deduplication
```python
window = Window.partitionBy("key_cols").orderBy("timestamp")
df.withColumn("rank", F.row_number().over(window)) \
  .filter(F.col("rank") == 1)
```

---

## 📊 Data Quality Summary

| Dataset | Bronze Records | Silver Records | Duplicates Removed | Invalid Data % |
|---------|----------------|----------------|--------------------|-----------------|
| EV Stations | 1,958 | 1,950 | 8 | 27% (missing kW) |
| Traffic Hazards | 431 | 429 | 2 | 13% (missing time) |
| Fuel Prices | 10,627 | 10,627 | 0 | 8.5% (invalid prices) |
| Weather | 20 | 20 | 0 | 0% |
| **Total** | **13,036** | **13,028** | **10** | **~12% avg** |

---

## 🛠️ Compute Requirements

- **Platform**: Databricks Serverless (CPU)
- **Runtime**: DBR 14.0+ with Unity Catalog
- **Memory**: 8GB+ recommended (gold layer cross-joins)
- **Processing Time**: ~10-12 minutes for full pipeline

---

## 📚 Layer-Specific Documentation

* [Bronze Layer README](bronze/README.md) - Ingestion details
* [Silver Layer README](silver/README.md) - Transformation logic
* [Gold Layer README](gold/README.md) - Analytics documentation

---

**Last Updated**: May 2026  
**Total Notebooks**: 10  
**Unity Catalog**: `mobility_ai` catalog