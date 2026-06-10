# Running DLT Pipeline in Parallel with Existing ETL

## 🎯 Objective

Run **Lakeflow Spark Declarative Pipeline (DLT)** alongside your existing notebook-based ETL.

---

## 📊 Your Current Tables

**Bronze**: `ev_charging_stations_raw`, `traffic_hazards_raw`, `fuel_raw`, `weather_raw`  
**Silver**: `ev_charging_stations`, `traffic_hazards`, `fuel_prices`, `weather_conditions`  
**Gold**: `regional_infrastructure_metrics`, `charger_recommendations_smart` (+ 8 more)

**Volume**: `/Volumes/mobility_ai/bronze/data_upload`

---

## 🔧 Parallel Strategy: Add `_dlt` Suffix

DLT will create **parallel tables** with `_dlt` suffix:

| Existing (Notebooks) | New (DLT Pipeline) |
|---------------------|-------------------|
| `ev_charging_stations_raw` | `ev_charging_stations_raw_dlt` |
| `ev_charging_stations` | `ev_charging_stations_dlt` |
| `regional_infrastructure_metrics` | `regional_infrastructure_metrics_dlt` |

---

## 📝 Changes Needed in Pipeline File

Edit `nsw_ev_medallion_pipeline.py`:

### 1. Add `_dlt` Suffix to All Table Names

**Bronze Layer** (4 tables):
```python
@dlt.table(name="ev_charging_stations_raw_dlt")  # Add _dlt
@dlt.table(name="traffic_hazards_raw_dlt")
@dlt.table(name="fuel_raw_dlt")
@dlt.table(name="weather_raw_dlt")
```

**Silver Layer** (4 tables):
```python
@dlt.table(name="ev_charging_stations_dlt")
@dlt.table(name="traffic_hazards_dlt")
@dlt.table(name="fuel_prices_dlt")
@dlt.table(name="weather_conditions_dlt")
```

**Gold Layer** (2 tables):
```python
@dlt.table(name="regional_infrastructure_metrics_dlt")
@dlt.table(name="charger_recommendations_smart_dlt")
```

### 2. Update Volume Path

```python
BRONZE_VOLUME_PATH = f"/Volumes/mobility_ai/bronze/data_upload"
```

### 3. Update `dlt.read_stream()` References

```python
# Silver reads from Bronze _dlt tables
dlt.read_stream("ev_charging_stations_raw_dlt")
dlt.read_stream("traffic_hazards_raw_dlt")
# etc...
```

### 4. Update SQL Queries (Gold Layer)

```sql
-- Change FROM LIVE.table_name to FROM LIVE.table_name_dlt
FROM LIVE.ev_charging_stations_dlt
FROM LIVE.traffic_hazards_dlt
```

---

## 🚀 Create DLT Pipeline

### In Databricks UI:

**Workflows** → **Delta Live Tables** → **Create Pipeline**

| Setting | Value |
|---------|-------|
| Pipeline Name | `NSW EV Intelligence - DLT (Parallel)` |
| Notebook | `pipelines/nsw_ev_medallion_pipeline.py` |
| Storage | `/pipelines/nsw_ev_intelligence_dlt` |
| Target Catalog | `mobility_ai` |
| Mode | Triggered |
| Workers | 1-3 (Enhanced Autoscaling) |

**Advanced**:
* ✅ Enable Auto Optimization
* ✅ Enable Schema Evolution

---

## 📊 Compare Results

```sql
-- Row count comparison
SELECT 'Existing' AS source, COUNT(*) FROM mobility_ai.silver.ev_charging_stations
UNION ALL
SELECT 'DLT' AS source, COUNT(*) FROM mobility_ai.silver.ev_charging_stations_dlt;

-- Schema comparison
DESCRIBE mobility_ai.silver.ev_charging_stations;
DESCRIBE mobility_ai.silver.ev_charging_stations_dlt;
```

---

## ✅ Validation Checklist

- [ ] Row counts match (±5%)
- [ ] Schemas identical
- [ ] DLT expectations passing (>95%)
- [ ] Performance comparable
- [ ] No pipeline failures

---

## 🔄 Both Systems Running

**Existing Notebook ETL**: Keep running on current schedule  
**New DLT Pipeline**: Run in parallel for 2-4 weeks

Monitor and compare before full migration.

---

**Status**: Ready to deploy! 🚀
