# Bronze Layer - Raw Data Ingestion

Raw data ingestion from NSW Government APIs into Delta Lake without transformation.

## 🎯 Purpose

Land data from external sources "as-is" with minimal processing:
- Preserve original schema and data types
- Add ingestion metadata (timestamp)
- Store in Delta Lake for ACID properties
- Enable schema evolution

## 📊 Notebooks (4 Total)

### 1. `ingest_ev_charging_stations.py`
**Data Source**: NSW EV Charging Stations API  
**Target Table**: `mobility_ai.bronze.ev_charging_stations_raw`  
**Record Count**: 1,958 stations  
**Refresh Frequency**: Weekly (infrastructure changes slowly)

**Schema Highlights**:
- `OBJECTID`, `StationName`, `StationAddress`
- `Latitude`, `Longitude`, `LGAName`
- `Operator`, `ChargerRating` (e.g., "50 kW")
- `ChargerType`, `ChargerPlacement`
- `ingestion_timestamp` (added)

**API Endpoint**: NSW Government Open Data Portal

---

### 2. `ingest_traffic_hazards.py`
**Data Source**: NSW Traffic Hazards API (Live Traffic NSW)  
**Target Table**: `mobility_ai.bronze.traffic_hazards_raw`  
**Record Count**: 431 hazards  
**Refresh Frequency**: Hourly (real-time conditions)

**Schema Highlights**:
- `hazardId`, `headline`, `hazardType`
- `latitude`, `longitude`, `lga`
- `isMajor`, `impact`, `isEnded`
- `start`, `end`, `created`, `lastUpdated`
- `mainCategory` (Roadwork, Incident, Flood, Special Event)
- `ingestion_timestamp` (added)

**API Endpoint**: Live Traffic NSW API

**Known Issues**:
- 100% of records have null `hazardId`
- 99% of roadwork entries lack `headline` descriptions
- 13% missing `start` timestamp (immediate events)

---

### 3. `ingest_fuel_prices.py`
**Data Source**: NSW Fuel Check API  
**Target Table**: `mobility_ai.bronze.fuel_raw`  
**Record Count**: 10,627 price records  
**Refresh Frequency**: Daily (prices updated daily)

**Schema Highlights**:
- `stationcode`, `brand`, `stationname`
- `address`, `suburb`, `postcode`
- `fueltype` (UNLEADED, DIESEL, LPG, etc.)
- `price` (cents per liter)
- `lastupdated` (DD/MM/YYYY HH:mm:ss format)
- `ingestion_timestamp` (added)

**API Endpoint**: NSW Fuel Check API

**Data Characteristics**:
- No lat/lon coordinates provided
- Multiple fuel types per station
- Prices in cents/liter (Australian standard)

---

### 4. `ingest_weather_conditions.py`
**Data Source**: Weather API  
**Target Table**: `mobility_ai.bronze.weather_raw`  
**Record Count**: 20 observation stations  
**Refresh Frequency**: Hourly (current conditions)

**Schema Highlights**:
- `station_id`, `station_name`
- `latitude`, `longitude`
- `temperature`, `humidity`, `precipitation`
- `wind_speed`, `wind_direction`
- `weather_condition`, `observation_time`
- `ingestion_timestamp` (added)

**API Endpoint**: Weather observation service

**Coverage**: NSW-wide observation network

---

## 🛠️ Common Ingestion Pattern

All bronze notebooks follow this structure:

```python
# 1. Configuration
API_URL = "..."
TARGET_TABLE = "mobility_ai.bronze.table_name"

# 2. Fetch data from API
response = requests.get(API_URL)
data = response.json()

# 3. Convert to Spark DataFrame
df = spark.read.json(spark.sparkContext.parallelize([data]))

# 4. Add metadata
df = df.withColumn("ingestion_timestamp", F.current_timestamp())

# 5. Write to Delta Lake
df.write \
    .format("delta") \
    .mode("overwrite")  # or "append" for incremental
    .saveAsTable(TARGET_TABLE)

# 6. Validation
count = spark.table(TARGET_TABLE).count()
print(f"Loaded {count:,} records")
```

---

## 📈 Data Volumes

| Notebook | Records | API Response Size | Delta Table Size |
|----------|---------|-------------------|-------------------|
| EV Charging Stations | 1,958 | ~800 KB | ~2 MB |
| Traffic Hazards | 431 | ~200 KB | ~500 KB |
| Fuel Prices | 10,627 | ~1.5 MB | ~3 MB |
| Weather Conditions | 20 | ~50 KB | ~100 KB |
| **Total** | **13,036** | **~2.5 MB** | **~5.6 MB** |

---

## 🔄 Recommended Refresh Schedule

```python
# Hourly (real-time conditions)
ingest_traffic_hazards.py    # Traffic changes frequently
ingest_weather_conditions.py # Weather updates hourly

# Daily
ingest_fuel_prices.py        # Prices updated daily

# Weekly
ingest_ev_charging_stations.py # Infrastructure changes slowly
```

**Cron Schedule Examples**:
```bash
# Hourly at minute 0
0 * * * * ingest_traffic_hazards.py
0 * * * * ingest_weather_conditions.py

# Daily at 2 AM
0 2 * * * ingest_fuel_prices.py

# Weekly on Sunday at 3 AM
0 3 * * 0 ingest_ev_charging_stations.py
```

---

## ⚠️ Known Data Quality Issues

### EV Charging Stations
- ✅ Complete: All stations have coordinates
- ⚠️ Partial: 27% have non-numeric charger ratings ("AC" only)

### Traffic Hazards
- ❌ Missing: 100% of records lack unique `hazardId`
- ❌ Missing: 99% of roadwork entries lack `headline`
- ⚠️ Partial: 13% missing `start` timestamp

### Fuel Prices
- ❌ Missing: No lat/lon coordinates provided by API
- ✅ Complete: All records have station code and price
- ⚠️ Invalid: 8.5% have prices outside valid range

### Weather Conditions
- ✅ Complete: All 20 stations have full metrics
- ✅ Complete: All have valid NSW coordinates

---

## 🔒 Data Governance

### Unity Catalog
- **Catalog**: `mobility_ai`
- **Schema**: `bronze`
- **Access**: Public NSW Government data

### Delta Lake Features
- **ACID Transactions**: Guaranteed write consistency
- **Time Travel**: 30-day retention (default)
- **Schema Evolution**: Enabled on all tables
- **Audit Trail**: `ingestion_timestamp` on every record

### Data Classification
- **Sensitivity**: Public
- **PII**: None
- **Licensing**: NSW Government Open Data

---

## 📚 Next Steps

After bronze ingestion:
1. **Silver Layer**: Transform and validate data
   - See [Silver Layer README](../silver/README.md)
2. **Data Quality**: Review validation results
3. **Monitoring**: Set up alerting for API failures

---

## 🔧 Error Handling

### API Failures
```python
try:
    response = requests.get(API_URL, timeout=30)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    print(f"API Error: {e}")
    # Alert monitoring system
```

### Schema Changes
```python
# Enable schema evolution
.option("mergeSchema", "true")
.option("overwriteSchema", "true")
```

---

**Last Updated**: May 2026  
**Total Notebooks**: 4  
**Total Records**: 13,036  
**Data Sources**: NSW Government APIs