# Deploy NSW EV Medallion Pipeline (Parallel Mode)

## 🎯 What Was Created

✅ **Pipeline Code**: `nsw-ev-intelligence/pipelines/nsw_ev_medallion_pipeline_parallel.py`  
✅ **Pipeline Config**: `resources/medallion_pipeline_parallel.pipeline.yml`  
✅ **Bundle Config**: Updated `databricks.yml` to include the new pipeline

---

## 📋 Deployment Options

### Option 1: Deploy with DABs (Recommended)

Use Databricks Asset Bundles to deploy the pipeline programmatically.

#### Step 1: Validate Bundle

From your **local machine** or **Databricks web terminal**:

```bash
cd /Workspace/Users/moeedk1@gmail.com/NSW-EV-Intelligence-Platform

# Validate configuration
databricks bundle validate --strict

# Expected output: Configuration validation successful
```

#### Step 2: Deploy Pipeline

```bash
# Deploy to dev environment (default)
databricks bundle deploy

# Or deploy to specific target
databricks bundle deploy --target dev
databricks bundle deploy --target staging
databricks bundle deploy --target prod
```

This will create the pipeline:
* **Dev**: `nsw-ev-medallion-parallel-dev`
* **Staging**: `nsw-ev-medallion-parallel-staging`
* **Prod**: `nsw-ev-medallion-parallel-prod`

#### Step 3: Start Pipeline

```bash
# Run the pipeline
databricks bundle run medallion_pipeline_parallel

# Or trigger via CLI directly
databricks pipelines start <pipeline-id>
```

---

### Option 2: Create Manually in UI

If you prefer to create the pipeline through the Databricks UI:

#### Step 1: Navigate to Workflows

**Databricks UI** → **Workflows** → **Delta Live Tables** → **Create Pipeline**

#### Step 2: Configure Pipeline

| Setting | Value |
|---------|-------|
| **Pipeline Name** | `nsw-ev-medallion-parallel-dev` |
| **Product Edition** | **Pro** (for data quality expectations) |
| **Pipeline Mode** | **Triggered** |
| **Notebook Path** | `/Users/moeedk1@gmail.com/NSW-EV-Intelligence-Platform/nsw-ev-intelligence/pipelines/nsw_ev_medallion_pipeline_parallel.py` |
| **Storage Location** | `/pipelines/nsw-ev-medallion-parallel/dev` |
| **Target Catalog** | `mobility_ai` |
| **Target Schema** | *(leave empty - defined in code)* |

#### Step 3: Compute Settings

| Setting | Value |
|---------|-------|
| **Cluster Mode** | **Enhanced Autoscaling** |
| **Min Workers** | 1 |
| **Max Workers** | 3 |
| **Photon Acceleration** | ✅ **Enabled** |

#### Step 4: Advanced Settings

* ✅ **Enable development mode**
* ✅ **Channel**: Preview (for latest DLT features)
* **Configuration** (optional):
  ```
  pipelines.autoOptimize.managed = true
  pipelines.clusterShutdown.delay = 30m
  spark.databricks.delta.schema.autoMerge.enabled = true
  ```

#### Step 5: Create & Start

1. Click **"Create"**
2. Click **"Start"** → **"Full Refresh"**
3. Monitor pipeline execution in the graph view

---

## 📊 Pipeline Architecture

### Tables Created (all with `_dlt` suffix):

**Bronze Layer** (4 tables):
* `mobility_ai.bronze.ev_charging_stations_raw_dlt`
* `mobility_ai.bronze.traffic_hazards_raw_dlt` ← STREAMING
* `mobility_ai.bronze.fuel_raw_dlt`
* `mobility_ai.bronze.weather_raw_dlt`

**Silver Layer** (4 tables):
* `mobility_ai.silver.ev_charging_stations_dlt`
* `mobility_ai.silver.traffic_hazards_dlt` ← STREAMING
* `mobility_ai.silver.fuel_prices_dlt`
* `mobility_ai.silver.weather_conditions_dlt`

**Gold Layer** (2 tables):
* `mobility_ai.gold.regional_infrastructure_metrics_dlt`
* `mobility_ai.gold.charger_recommendations_smart_dlt`

---

## 🔄 Running in Parallel

Your **existing notebook-based ETL** continues running alongside this DLT pipeline:

| Layer | Existing Tables | DLT Tables (Parallel) |
|-------|----------------|----------------------|
| **Bronze** | `ev_charging_stations_raw` | `ev_charging_stations_raw_dlt` |
| **Silver** | `ev_charging_stations` | `ev_charging_stations_dlt` |
| **Gold** | `regional_infrastructure_metrics` | `regional_infrastructure_metrics_dlt` |

Both systems read from the same volume:
* **Volume**: `/Volumes/mobility_ai/bronze/data_upload`

---

## ✅ Post-Deployment Validation

### 1. Check Pipeline Status

```bash
# List all pipelines
databricks pipelines list

# Get pipeline details
databricks pipelines get <pipeline-id>

# View events
databricks pipelines list-events <pipeline-id>
```

### 2. Verify Tables Created

```sql
-- List DLT tables
SHOW TABLES IN mobility_ai.bronze LIKE '%_dlt';
SHOW TABLES IN mobility_ai.silver LIKE '%_dlt';
SHOW TABLES IN mobility_ai.gold LIKE '%_dlt';
```

### 3. Compare Row Counts

```sql
-- Bronze layer comparison
SELECT 'Notebook ETL' AS source, COUNT(*) AS rows 
FROM mobility_ai.bronze.ev_charging_stations_raw
UNION ALL
SELECT 'DLT Pipeline' AS source, COUNT(*) AS rows 
FROM mobility_ai.bronze.ev_charging_stations_raw_dlt;

-- Silver layer comparison
SELECT 'Notebook ETL' AS source, COUNT(*) AS rows 
FROM mobility_ai.silver.ev_charging_stations
UNION ALL
SELECT 'DLT Pipeline' AS source, COUNT(*) AS rows 
FROM mobility_ai.silver.ev_charging_stations_dlt;
```

### 4. Check Data Quality Expectations

In the **DLT Pipeline UI**:
* Navigate to **Data Quality** tab
* Review **expectation metrics**:
  * Records passed
  * Records dropped
  * Expectation violation details

---

## 🐛 Troubleshooting

### Issue: Pipeline validation fails

**Solution**: Check YAML syntax
```bash
cd /Workspace/Users/moeedk1@gmail.com/NSW-EV-Intelligence-Platform
databricks bundle validate --strict
```

### Issue: Tables not created after first run

**Cause**: Source files not found

**Solution**: Check volume paths
```sql
-- Verify files exist
LIST '/Volumes/mobility_ai/bronze/data_upload/ev_stations/';
LIST '/Volumes/mobility_ai/bronze/data_upload/traffic_hazards/';
LIST '/Volumes/mobility_ai/bronze/data_upload/fuel/';
LIST '/Volumes/mobility_ai/bronze/data_upload/weather/';
```

### Issue: Schema conflicts

**Cause**: DLT inferring different schema

**Solution**: Check Auto Loader schema hints in the pipeline code (already configured)

### Issue: Expectations dropping all records

**Cause**: Expectations too strict

**Solution**: Check DLT UI for expectation details and adjust accordingly

---

## 🚀 Next Steps

### 1. Full Refresh (First Run)

```bash
databricks bundle run medallion_pipeline_parallel --full-refresh
```

This will:
* ✅ Process all existing source files
* ✅ Create all 10 tables (4 bronze + 4 silver + 2 gold)
* ✅ Apply data quality expectations
* ✅ Populate initial data

### 2. Monitor Pipeline

* **DLT UI**: View execution graph, metrics, data quality
* **Tables**: Query tables to validate data
* **Logs**: Check for any errors or warnings

### 3. Compare with Existing ETL

Run validation queries (see above) to compare:
* Row counts
* Data quality
* Schema consistency
* Processing timestamps

### 4. Set Up Schedule (Optional)

For recurring execution:

**Option A: Add to databricks.yml**
```yaml
pipelines:
  medallion_pipeline_parallel:
    # ... existing config ...
    trigger:
      cron:
        quartz_cron_expression: "0 0 */6 * * ?" # Every 6 hours
        timezone_id: "UTC"
```

**Option B: Via CLI**
```bash
databricks jobs create --json @- <<EOF
{
  "name": "DLT Medallion Pipeline Schedule",
  "pipeline_task": {
    "pipeline_id": "<pipeline-id>",
    "full_refresh": false
  },
  "schedule": {
    "quartz_cron_expression": "0 0 */6 * * ?",
    "timezone_id": "UTC"
  }
}
EOF
```

---

## 📚 Useful Commands

```bash
# Bundle operations
databricks bundle validate
databricks bundle deploy
databricks bundle run medallion_pipeline_parallel
databricks bundle destroy  # Careful! Removes all resources

# Pipeline operations
databricks pipelines list
databricks pipelines get <pipeline-id>
databricks pipelines start <pipeline-id>
databricks pipelines stop <pipeline-id>
databricks pipelines reset <pipeline-id>  # Full refresh
databricks pipelines list-events <pipeline-id>

# View pipeline details
databricks pipelines get <pipeline-id> --output json
```

---

## 🎯 Success Criteria

Pipeline is ready when:

* ✅ Deployment successful (no validation errors)
* ✅ First full refresh completes without errors
* ✅ All 10 tables created with `_dlt` suffix
* ✅ Data quality expectations passing (>95%)
* ✅ Row counts match existing ETL (±5%)
* ✅ No pipeline failures for 24 hours

---

**Status**: Ready to deploy! 🚀

**Last Updated**: Current deployment
