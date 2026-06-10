# NSW EV Intelligence - Lakeflow Spark Declarative Pipeline

Comprehensive data pipeline using **Lakeflow Spark Declarative Pipelines** (formerly Delta Live Tables) with mixed streaming and batch processing.

---

## 🏗️ Pipeline Architecture

### **Medallion Structure**: Bronze → Silver → Gold

```
┌─────────────────────────────────────────────────────────────┐
│                      BRONZE LAYER (Raw)                      │
├─────────────────────────────────────────────────────────────┤
│  🔵 ev_charging_stations_raw  (Batch - Auto Loader)         │
│  🔴 traffic_hazards_raw       (Streaming - Auto Loader)     │
│  🔵 fuel_raw                  (Batch - Auto Loader)         │
│  🔵 weather_raw               (Batch - Auto Loader)         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  SILVER LAYER (Cleaned)                      │
├─────────────────────────────────────────────────────────────┤
│  ✅ ev_charging_stations   (Quality expectations)           │
│  ✅ traffic_hazards        (Streaming + Expectations)       │
│  ✅ fuel_prices            (Quality expectations)           │
│  ✅ weather_conditions     (Quality expectations)           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              GOLD LAYER (Business Intelligence)              │
├─────────────────────────────────────────────────────────────┤
│  📊 regional_infrastructure_metrics                         │
│  📊 charger_recommendations_smart                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔴🔵 Streaming vs Batch Strategy

| Data Source | Mode | Update Frequency | Reason |
|-------------|------|------------------|--------|
| **Traffic Hazards** | 🔴 **STREAMING** | Real-time (minutes) | Live traffic changes constantly, need immediate updates |
| **EV Stations** | 🔵 **BATCH** | Infrequent (days/weeks) | Stations rarely change, batch sufficient |
| **Fuel Prices** | 🔵 **BATCH** | Daily | Prices update once per day |
| **Weather** | 🔵 **BATCH** | Hourly | Hourly updates are sufficient |

---

## 📋 Pipeline File

**Location**: `pipelines/nsw_ev_medallion_pipeline.py`

**Contents**:
* **Bronze Layer** - Auto Loader ingestion (4 tables)
* **Silver Layer** - Transformations + Expectations (4 tables)
* **Gold Layer** - Business analytics (2 tables)

---

## 🚀 Setup Instructions

### Step 1: Prepare Data Landing Zone

**Option A: Unity Catalog Volumes** (Recommended)

```sql
-- Create volumes for raw data
CREATE VOLUME IF NOT EXISTS mobility_ai.bronze.raw_data;

-- Create subdirectories (use Databricks File Explorer or dbutils)
```

**Directory structure**:
```
/Volumes/mobility_ai/bronze/raw_data/
  ├── ev_stations/           # JSON files from EV API
  ├── traffic_hazards/       # JSON files from Traffic API
  ├── fuel/                  # JSON files from Fuel API
  └── weather/               # JSON files from Weather API
```

**Option B: Cloud Storage**

Update `BRONZE_VOLUME_PATH` in pipeline to point to S3/ADLS/GCS:
```python
BRONZE_VOLUME_PATH = "s3://your-bucket/nsw-ev-data/raw/"
```

---

### Step 2: Create Pipeline in Databricks UI

1. **Navigate to Workflows** → **Delta Live Tables**

2. **Click "Create Pipeline"**

3. **Configure Pipeline**:

| Setting | Value |
|---------|-------|
| **Pipeline Name** | `NSW EV Intelligence Pipeline` |
| **Product Edition** | Pro or Advanced (for expectations) |
| **Pipeline Mode** | Triggered (for batch) or Continuous (for streaming) |
| **Notebook** | Select `pipelines/nsw_ev_medallion_pipeline.py` |
| **Storage Location** | `/pipelines/nsw_ev_intelligence` |
| **Target Catalog** | `mobility_ai` |
| **Target Schema** | Leave empty (defined in code) |

4. **Compute Settings**:
   * **Cluster Mode**: Enhanced Autoscaling
   * **Min Workers**: 1
   * **Max Workers**: 5
   * **Cluster Policy**: (optional) Select compute policy

5. **Advanced Settings**:
   * **Enable Auto Optimization**: ✅ Checked
   * **Enable Schema Evolution**: ✅ Checked

6. **Click "Create"**

---

### Step 3: Configure Data Ingestion

You need to set up a process to land API data into the raw data volumes:

**Option A: Databricks Job** (Recommended)

Create a scheduled job that:
1. Calls NSW Transport APIs
2. Writes JSON files to volumes
3. Runs hourly/daily based on data source

**Example notebook for API ingestion**:

```python
import requests
import json
from datetime import datetime

# EV Stations API
def ingest_ev_stations():
    response = requests.get("https://api.transport.nsw.gov.au/v1/carpark")
    data = response.json()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"/Volumes/mobility_ai/bronze/raw_data/ev_stations/ev_{timestamp}.json"
    
    dbutils.fs.put(path, json.dumps(data), overwrite=True)
    print(f"✅ Ingested EV stations to {path}")

# Traffic Hazards API (streaming - run frequently)
def ingest_traffic_hazards():
    response = requests.get("https://api.transport.nsw.gov.au/v1/live/hazards")
    data = response.json()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"/Volumes/mobility_ai/bronze/raw_data/traffic_hazards/traffic_{timestamp}.json"
    
    dbutils.fs.put(path, json.dumps(data), overwrite=True)
    print(f"✅ Ingested traffic hazards to {path}")

# Run ingestion
ingest_ev_stations()
ingest_traffic_hazards()
```

**Schedule this notebook**:
* **EV Stations**: Daily at 2 AM
* **Traffic Hazards**: Every 5 minutes (for streaming)
* **Fuel Prices**: Daily at 6 AM
* **Weather**: Hourly

**Option B: External Orchestration**

Use Airflow, Prefect, or similar to call APIs and write to volumes.

---

### Step 4: Run the Pipeline

**Initial Run** (Full Refresh):

1. Go to your pipeline in Databricks UI
2. Click **"Start"**
3. Select **"Full Refresh"** for first run
4. Monitor progress in the pipeline graph

**Expected Runtime**: 10-15 minutes for initial load

**Subsequent Runs** (Incremental):

Auto Loader will detect new files automatically:

1. **Triggered Mode**: Click "Start" manually when ready
2. **Continuous Mode**: Pipeline runs automatically

---

## 📊 Pipeline Monitoring

### View Pipeline Status

1. Navigate to your pipeline
2. View the **Pipeline Graph**:
   * 🟢 Green = Success
   * 🔴 Red = Failed
   * 🟡 Yellow = Running

### Check Data Quality Expectations

Click on any Silver table to view:
* **Records Passed**: Met all expectations
* **Records Dropped**: Failed expectations
* **Expectation Details**: Which rules failed

### Monitor Streaming Tables

For `traffic_hazards` (streaming):
* View **Input Rate** (records/second)
* View **Processing Rate**
* Check **Lag** (should be low)

---

## 🔧 Configuration Options

### Change Processing Mode

Edit pipeline settings:

**Triggered Mode** (Batch):
* Pipeline runs on-demand or scheduled
* Good for: Daily/hourly batch processing
* Lower cost (compute only when running)

**Continuous Mode** (Streaming):
* Pipeline runs 24/7
* Good for: Real-time traffic hazards
* Higher cost (always-on compute)

**Recommendation**: Start with **Triggered** mode, run every 5-15 minutes for near-real-time.

### Adjust Auto Loader Schema Inference

If data schema changes, Auto Loader will handle it automatically. To customize:

```python
.option("cloudFiles.schemaEvolutionMode", "rescue")  # Put new columns in _rescued_data
.option("cloudFiles.inferColumnTypes", "false")      # Disable type inference
```

---

## 🧪 Testing the Pipeline

### Test with Sample Data

1. **Create sample JSON files**:

```bash
# Sample EV station
cat > /Volumes/mobility_ai/bronze/raw_data/ev_stations/test_001.json << EOF
{
  "StationID": "TEST001",
  "OperatorName": "Test Operator",
  "AddressLine1": "123 Test St",
  "Suburb": "Sydney",
  "State": "NSW",
  "Postcode": "2000",
  "Latitude": -33.8688,
  "Longitude": 151.2093,
  "NumberOfPlugs": 4,
  "ChargerType": "DC",
  "ChargingPowerKW": 50
}
EOF
```

2. **Run pipeline** and verify:
   * Bronze table has 1 record
   * Silver table has 1 record (passed expectations)
   * Gold tables updated

3. **Delete test data** and re-run with full refresh

---

## 🐛 Troubleshooting

### Issue: "No data found in source"

**Cause**: Source paths are empty

**Solution**: 
1. Verify files exist in source volumes
2. Check path configuration in pipeline code
3. Run API ingestion job first

### Issue: "Records dropped by expectations"

**Cause**: Data quality issues

**Solution**:
1. Click on Silver table in pipeline graph
2. View **Expectations** tab
3. See which records failed and why
4. Fix data quality at source or adjust expectations

### Issue: "Streaming lag increasing"

**Cause**: Processing slower than ingestion

**Solution**:
1. Increase cluster size (max workers)
2. Optimize transformations
3. Add more partitions

### Issue: "Pipeline stuck on startup"

**Cause**: Cluster provisioning delay

**Solution**:
1. Wait 5-10 minutes for cluster startup
2. Use a cluster policy to pre-warm nodes
3. Consider using a shared cluster pool

---

## 📈 Performance Optimization

### Enable Predictive Optimization

```sql
ALTER TABLE mobility_ai.silver.ev_charging_stations 
SET TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true');
```

### Liquid Clustering (for Gold tables)

```sql
ALTER TABLE mobility_ai.gold.charger_recommendations_smart
CLUSTER BY (region, recommendation_tier);
```

### Z-Ordering (alternative to Liquid Clustering)

```sql
OPTIMIZE mobility_ai.gold.regional_infrastructure_metrics
ZORDER BY (region);
```

---

## 🔄 Pipeline Maintenance

### Full Refresh (Reset All Data)

1. Navigate to pipeline
2. Click **"⋮"** menu → **"Full Refresh"**
3. Confirm (this will delete and rebuild all tables)

**Use when**:
* Schema changes significantly
* Data corruption
* Testing major changes

### Partial Refresh (Specific Tables)

1. Click on specific table in pipeline graph
2. Click **"⋮"** → **"Refresh"**
3. Only that table and downstream dependencies refresh

---

## 📚 Additional Resources

* [Databricks Lakeflow Pipelines Documentation](https://docs.databricks.com/en/delta-live-tables/index.html)
* [Auto Loader Guide](https://docs.databricks.com/en/ingestion/auto-loader/index.html)
* [Data Quality Expectations](https://docs.databricks.com/en/delta-live-tables/expectations.html)
* [Streaming Best Practices](https://docs.databricks.com/en/structured-streaming/index.html)

---

## 🎯 Next Steps

1. ✅ **Create the pipeline** in Databricks UI
2. ✅ **Set up data ingestion** job for API calls
3. ✅ **Run initial full refresh** to populate tables
4. ✅ **Schedule recurring runs** (Triggered mode)
5. ✅ **Monitor data quality** via expectations
6. ✅ **Optimize performance** as data grows

---

**Pipeline Status**: Ready to deploy! 🚀

**Last Updated**: June 11, 2026
