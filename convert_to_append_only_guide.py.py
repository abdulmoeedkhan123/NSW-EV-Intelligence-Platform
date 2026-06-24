# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Guide: Converting to Append-Only Tables
# MAGIC %md
# MAGIC # Guide: Converting Tables to Append-Only with Time Partitioning
# MAGIC
# MAGIC This notebook provides patterns for converting your NSW EV Intelligence tables from **snapshot** (overwrite) to **append-only** (insert) with proper time-based partitioning.
# MAGIC
# MAGIC ## Why Append-Only?
# MAGIC
# MAGIC **Benefits:**
# MAGIC * 📊 **Historical Analysis** - Track trends over time
# MAGIC * 🔍 **Auditing** - See what data looked like at any point
# MAGIC * 🤖 **ML Training** - More data for model training
# MAGIC * 📈 **Forecasting** - Compare predictions vs actuals
# MAGIC * 🐛 **Debugging** - Trace data quality issues back in time
# MAGIC
# MAGIC **When to Use:**
# MAGIC * Time-series data (traffic, weather, fuel prices)
# MAGIC * Event data (hazards, incidents)
# MAGIC * Forecast/prediction outputs
# MAGIC * Any data where history matters
# MAGIC
# MAGIC **When NOT to Use:**
# MAGIC * Reference data that changes infrequently (charging stations)
# MAGIC * Dashboard snapshots showing current state only
# MAGIC * Tables that are recomputed from scratch each run

# COMMAND ----------

# DBTITLE 1,Pattern 1: Bronze Layer - Add Ingestion Timestamp
# Pattern 1: Bronze Layer Append-Only
# Add ingestion_date partition for efficient time-based queries

from pyspark.sql import functions as F

# Example: Converting fuel_raw to append-only
BRONZE_SOURCE = "mobility_ai.bronze.fuel_raw"  # Current snapshot table
BRONZE_APPEND = "mobility_ai.bronze.fuel_raw_history"  # New append-only table

# Read new data from source API
new_data = spark.table(BRONZE_SOURCE)  # In real pipeline, this comes from API

# Add ingestion metadata
append_df = new_data \
    .withColumn("ingestion_date", F.current_date()) \
    .withColumn("ingestion_timestamp", F.current_timestamp()) \
    .withColumn("pipeline_run_id", F.lit("<job_run_id>"))  # Track which job run ingested this

# Write with date partitioning for efficient time-based queries
append_df.write \
    .format("delta") \
    .mode("append") \
    .partitionBy("ingestion_date") \
    .saveAsTable(BRONZE_APPEND)

print(f"✅ Appended {append_df.count()} records to {BRONZE_APPEND}")

# COMMAND ----------

# DBTITLE 1,Pattern 2: Silver Layer - Business Date Partitioning
# Pattern 2: Silver Layer with Business Date
# Partition by the business/event date, not ingestion date

# Example: Converting traffic_conditions to append-only
SILVER_SOURCE = "mobility_ai.silver.traffic_conditions"
SILVER_APPEND = "mobility_ai.silver.traffic_conditions_history"

silver_df = spark.table(SILVER_SOURCE)

# Add business date from timestamp column if available
append_df = silver_df \
    .withColumn("report_date", F.to_date(F.col("timestamp"))) \
    .withColumn("processed_at", F.current_timestamp())

# Partition by report_date (the business date)
append_df.write \
    .format("delta") \
    .mode("append") \
    .partitionBy("report_date") \
    .saveAsTable(SILVER_APPEND)

print(f"✅ Appended {append_df.count()} records to {SILVER_APPEND}")

# Query pattern: Get last 7 days of traffic
# SELECT * FROM mobility_ai.silver.traffic_conditions_history 
# WHERE report_date >= CURRENT_DATE - INTERVAL 7 DAYS

# COMMAND ----------

# DBTITLE 1,Pattern 3: Gold Layer - Snapshot History
# Pattern 3: Gold Layer - Keep Daily Snapshots
# Store daily snapshots of forecasts/recommendations for accuracy tracking

# Example: Converting congestion_forecast to append-only
GOLD_SOURCE = "mobility_ai.gold.congestion_forecast_hourly"
GOLD_APPEND = "mobility_ai.gold.congestion_forecast_history"

forecast_df = spark.table(GOLD_SOURCE)

# Add snapshot metadata
append_df = forecast_df \
    .withColumn("forecast_date", F.current_date()) \
    .withColumn("forecast_timestamp", F.current_timestamp()) \
    .withColumn("model_version", F.lit("v1.0"))  # Track model changes

# Partition by forecast_date
append_df.write \
    .format("delta") \
    .mode("append") \
    .partitionBy("forecast_date") \
    .saveAsTable(GOLD_APPEND)

print(f"✅ Appended {append_df.count()} forecasts to {GOLD_APPEND}")

# Use case: Compare forecast accuracy over time
# SELECT forecast_date, predicted_congestion, actual_congestion
# FROM gold.congestion_forecast_history
# WHERE forecast_date >= '2026-06-01'

# COMMAND ----------

# DBTITLE 1,Pattern 4: Deduplication Strategy
# Pattern 4: Append-Only with Deduplication
# Handle duplicate ingestion using MERGE

# Example: Fuel prices with deduplication on (stationcode, fueltype, date)
from delta.tables import DeltaTable

TARGET_TABLE = "mobility_ai.bronze.fuel_raw_history"

# New data to append
new_fuel_data = spark.table("mobility_ai.bronze.fuel_raw") \
    .withColumn("ingestion_date", F.current_date())

# Check if table exists
if spark.catalog.tableExists(TARGET_TABLE):
    # Use MERGE to avoid duplicates
    target = DeltaTable.forName(spark, TARGET_TABLE)
    
    target.alias("target").merge(
        new_fuel_data.alias("source"),
        # Match on business key + date
        "target.stationcode = source.stationcode AND " +
        "target.fueltype = source.fueltype AND " +
        "target.ingestion_date = source.ingestion_date"
    ).whenNotMatchedInsertAll().execute()
    
    print("✅ Merged new fuel price records (deduplicated)")
else:
    # First load - just write
    new_fuel_data.write \
        .format("delta") \
        .mode("overwrite") \
        .partitionBy("ingestion_date") \
        .saveAsTable(TARGET_TABLE)
    print("✅ Created initial table")

# COMMAND ----------

# DBTITLE 1,Pattern 5: Time Travel Queries
# MAGIC %sql
# MAGIC -- Pattern 5: Querying Append-Only Tables
# MAGIC
# MAGIC -- Get latest snapshot (most recent data)
# MAGIC SELECT *
# MAGIC FROM mobility_ai.bronze.fuel_raw_history
# MAGIC WHERE ingestion_date = (SELECT MAX(ingestion_date) FROM mobility_ai.bronze.fuel_raw_history);
# MAGIC
# MAGIC -- Get data from specific date
# MAGIC SELECT *
# MAGIC FROM mobility_ai.bronze.fuel_raw_history
# MAGIC WHERE ingestion_date = '2026-06-24';
# MAGIC
# MAGIC -- Get data range (last 7 days)
# MAGIC SELECT *
# MAGIC FROM mobility_ai.bronze.fuel_raw_history
# MAGIC WHERE ingestion_date >= CURRENT_DATE - INTERVAL 7 DAYS;
# MAGIC
# MAGIC -- Track how a specific station's price changed over time
# MAGIC SELECT 
# MAGIC     ingestion_date,
# MAGIC     stationcode,
# MAGIC     fueltype,
# MAGIC     price
# MAGIC FROM mobility_ai.bronze.fuel_raw_history
# MAGIC WHERE stationcode = '123'
# MAGIC   AND fueltype = 'E10'
# MAGIC ORDER BY ingestion_date DESC;
# MAGIC
# MAGIC -- Compare forecast vs actual (requires joining forecast history with actuals)
# MAGIC SELECT 
# MAGIC     f.forecast_date,
# MAGIC     f.location_id,
# MAGIC     f.predicted_congestion,
# MAGIC     a.actual_congestion,
# MAGIC     ABS(f.predicted_congestion - a.actual_congestion) as error
# MAGIC FROM mobility_ai.gold.congestion_forecast_history f
# MAGIC JOIN mobility_ai.silver.traffic_conditions_history a
# MAGIC   ON f.location_id = a.location_id
# MAGIC   AND f.forecast_date = a.report_date
# MAGIC WHERE f.forecast_date >= '2026-06-01';

# COMMAND ----------

# DBTITLE 1,Recommended Conversion Priority
# MAGIC %md
# MAGIC ## 🎯 Recommended Conversion Order
# MAGIC
# MAGIC ### **Phase 1: Bronze Layer (Highest Priority)**
# MAGIC These preserve raw data history for reprocessing:
# MAGIC 1. ✅ `fuel_raw` → `fuel_raw_history` (daily price trends)
# MAGIC 2. ✅ `traffic_raw` → `traffic_raw_history` (traffic patterns)
# MAGIC 3. ✅ `weather_raw` → `weather_raw_history` (weather correlations)
# MAGIC 4. ✅ `traffic_hazards_raw` → `traffic_hazards_history` (incident patterns)
# MAGIC
# MAGIC ### **Phase 2: Silver Layer Time-Series**
# MAGIC Critical for trend analysis:
# MAGIC 1. ✅ `traffic_conditions` → `traffic_conditions_history`
# MAGIC 2. ✅ `weather_conditions` → `weather_conditions_history`
# MAGIC 3. ✅ `fuel_prices` → `fuel_prices_history`
# MAGIC
# MAGIC ### **Phase 3: Gold Layer Forecasts**
# MAGIC Track model performance:
# MAGIC 1. ✅ `congestion_forecast_hourly` → `congestion_forecast_history`
# MAGIC 2. ✅ `trip_recommendations` → `trip_recommendations_history`
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 🚀 Migration Strategy
# MAGIC
# MAGIC **Option A: Parallel Tables (Safest)**
# MAGIC * Create new `_history` tables alongside existing ones
# MAGIC * Run both in parallel for 30 days
# MAGIC * Validate data quality and query performance
# MAGIC * Deprecate old tables
# MAGIC
# MAGIC **Option B: Rename & Backfill**
# MAGIC * Rename current table to `_snapshot`
# MAGIC * Create new append-only table with original name
# MAGIC * Backfill with current data as first partition
# MAGIC * Update pipeline to append
# MAGIC
# MAGIC **Option C: In-Place Conversion**
# MAGIC * Add date column to existing table
# MAGIC * Change write mode from `overwrite` to `append`
# MAGIC * ⚠️ Risk: Can't easily go back

# COMMAND ----------

# DBTITLE 1,Option A Implementation: Parallel Tables
# MAGIC %md
# MAGIC ## 🔧 Option A Implementation: Parallel Tables
# MAGIC
# MAGIC ### Strategy Overview
# MAGIC 1. Create new `_history` tables
# MAGIC 2. Modify ingestion notebooks to write to **BOTH** tables
# MAGIC 3. Run in parallel for 30 days
# MAGIC 4. Compare data quality and query performance
# MAGIC 5. Switch queries to history tables
# MAGIC 6. Deprecate snapshot tables
# MAGIC
# MAGIC ### Benefits
# MAGIC - ✅ Zero downtime - existing tables keep working
# MAGIC - ✅ Easy rollback - just stop writing to history tables
# MAGIC - ✅ Validation period - compare data between both tables
# MAGIC - ✅ Gradual migration - move queries one at a time

# COMMAND ----------

# DBTITLE 1,Phase 1: Create Bronze History Tables
# Phase 1: Create Bronze Layer History Tables
# This creates the schema for all bronze history tables

from pyspark.sql import functions as F

print("="*80)
print("Creating Bronze Layer History Tables")
print("="*80)

# Configuration
BRONZE_TABLES = [
    "fuel_raw",
    "traffic_raw",
    "weather_raw",
    "traffic_hazards_raw",
    "ev_charging_stations_raw"
]

for table_name in BRONZE_TABLES:
    source_table = f"mobility_ai.bronze.{table_name}"
    history_table = f"mobility_ai.bronze.{table_name}_history"
    
    print(f"\n📊 Creating {history_table}...")
    
    # Read current snapshot
    snapshot_df = spark.table(source_table)
    
    # Add history metadata
    history_df = snapshot_df \
        .withColumn("ingestion_date", F.current_date()) \
        .withColumn("ingestion_timestamp", F.current_timestamp()) \
        .withColumn("pipeline_run_id", F.lit("initial_load"))
    
    # Create history table with initial load
    history_df.write \
        .format("delta") \
        .mode("overwrite") \
        .partitionBy("ingestion_date") \
        .option("overwriteSchema", "true") \
        .saveAsTable(history_table)
    
    record_count = history_df.count()
    print(f"   ✅ Created with {record_count:,} initial records")

print("\n" + "="*80)
print("✅ All Bronze history tables created!")
print("="*80)

# COMMAND ----------

# DBTITLE 1,Helper Function: Dual Write Pattern
# Helper Function: Write to Both Snapshot and History Tables
# Add this to your ingestion notebooks

def write_dual_tables(df, catalog, schema, table_name, mode="overwrite", partition_col=None):
    """
    Write dataframe to both snapshot and history tables.
    
    Args:
        df: DataFrame to write
        catalog: Catalog name (e.g., 'mobility_ai')
        schema: Schema name (e.g., 'bronze', 'silver', 'gold')
        table_name: Base table name without _history suffix
        mode: Write mode for snapshot table ('overwrite' or 'append')
        partition_col: Column name to partition history table (default: 'ingestion_date')
    """
    from pyspark.sql import functions as F
    
    snapshot_table = f"{catalog}.{schema}.{table_name}"
    history_table = f"{catalog}.{schema}.{table_name}_history"
    
    print(f"\n📝 Writing to dual tables: {table_name}")
    print("─" * 60)
    
    # 1. Write to snapshot table (overwrite)
    print(f"   1️⃣ Writing to snapshot: {snapshot_table}")
    df.write \
        .format("delta") \
        .mode(mode) \
        .option("overwriteSchema", "true") \
        .saveAsTable(snapshot_table)
    
    snapshot_count = spark.table(snapshot_table).count()
    print(f"      ✅ Snapshot: {snapshot_count:,} records")
    
    # 2. Add metadata and write to history table (append)
    print(f"   2️⃣ Appending to history: {history_table}")
    
    history_df = df \
        .withColumn("ingestion_date", F.current_date()) \
        .withColumn("ingestion_timestamp", F.current_timestamp())
    
    # Add job context if available
    try:
        from pyspark.dbutils import DBUtils
        dbutils = DBUtils(spark)
        job_run_id = dbutils.notebook.entry_point.getDbutils().notebook().getContext().tags().get("jobId").getOrElse("manual")
        history_df = history_df.withColumn("pipeline_run_id", F.lit(job_run_id))
    except:
        history_df = history_df.withColumn("pipeline_run_id", F.lit("unknown"))
    
    # Write with partitioning
    partition_cols = [partition_col] if partition_col else ["ingestion_date"]
    
    history_df.write \
        .format("delta") \
        .mode("append") \
        .partitionBy(*partition_cols) \
        .saveAsTable(history_table)
    
    history_count = spark.table(history_table).count()
    print(f"      ✅ History: {history_count:,} total records")
    print("─" * 60)
    
    return snapshot_count, history_count

print("✅ Dual write helper function defined")

# COMMAND ----------

# DBTITLE 1,Example: Update Bronze Fuel Ingestion
# Example: Modify Bronze Fuel Ingestion to Write Both Tables
# This shows how to update your existing notebook

# BEFORE (your current code):
# df.write.format("delta").mode("overwrite").saveAsTable("mobility_ai.bronze.fuel_raw")

# AFTER (dual write):
from pyspark.sql import functions as F

# Assuming you already have your ingested data in 'fuel_df'
# fuel_df = ... your API ingestion code ...

# For demo, let's load current data
fuel_df = spark.table("mobility_ai.bronze.fuel_raw")

print("\n" + "="*80)
print("Bronze Fuel Ingestion - Dual Write")
print("="*80)

# Write to both tables
write_dual_tables(
    df=fuel_df,
    catalog="mobility_ai",
    schema="bronze",
    table_name="fuel_raw",
    mode="overwrite"
)

print("\n✅ Fuel data written to both snapshot and history tables")

# COMMAND ----------

# DBTITLE 1,Validation Queries
# MAGIC %sql
# MAGIC -- Validation: Compare Snapshot vs History Tables
# MAGIC
# MAGIC -- Check record counts match for today's load
# MAGIC SELECT 
# MAGIC     'Snapshot' as table_type,
# MAGIC     COUNT(*) as record_count
# MAGIC FROM mobility_ai.bronze.fuel_raw
# MAGIC
# MAGIC UNION ALL
# MAGIC
# MAGIC SELECT 
# MAGIC     'History (Today)' as table_type,
# MAGIC     COUNT(*) as record_count
# MAGIC FROM mobility_ai.bronze.fuel_raw_history
# MAGIC WHERE ingestion_date = CURRENT_DATE;
# MAGIC
# MAGIC -- Compare data quality between tables
# MAGIC WITH snapshot_stats AS (
# MAGIC     SELECT 
# MAGIC         COUNT(*) as total_records,
# MAGIC         COUNT(DISTINCT stationcode) as unique_stations,
# MAGIC         AVG(price) as avg_price
# MAGIC     FROM mobility_ai.bronze.fuel_raw
# MAGIC ),
# MAGIC history_stats AS (
# MAGIC     SELECT 
# MAGIC         COUNT(*) as total_records,
# MAGIC         COUNT(DISTINCT stationcode) as unique_stations,
# MAGIC         AVG(price) as avg_price
# MAGIC     FROM mobility_ai.bronze.fuel_raw_history
# MAGIC     WHERE ingestion_date = CURRENT_DATE
# MAGIC )
# MAGIC SELECT 
# MAGIC     'Snapshot' as source,
# MAGIC     s.total_records,
# MAGIC     s.unique_stations,
# MAGIC     ROUND(s.avg_price, 2) as avg_price
# MAGIC FROM snapshot_stats s
# MAGIC UNION ALL
# MAGIC SELECT 
# MAGIC     'History' as source,
# MAGIC     h.total_records,
# MAGIC     h.unique_stations,
# MAGIC     ROUND(h.avg_price, 2) as avg_price
# MAGIC FROM history_stats h;
# MAGIC
# MAGIC -- View history growth over time
# MAGIC SELECT 
# MAGIC     ingestion_date,
# MAGIC     COUNT(*) as records_ingested,
# MAGIC     COUNT(DISTINCT stationcode) as unique_stations
# MAGIC FROM mobility_ai.bronze.fuel_raw_history
# MAGIC GROUP BY ingestion_date
# MAGIC ORDER BY ingestion_date DESC
# MAGIC LIMIT 10;

# COMMAND ----------

# DBTITLE 1,Migration Checklist
# MAGIC %md
# MAGIC ## ✅ Migration Checklist
# MAGIC
# MAGIC ### Week 1: Setup (Days 1-3)
# MAGIC - [ ] Run **Phase 1** to create all bronze `_history` tables
# MAGIC - [ ] Add `write_dual_tables()` helper function to shared utilities
# MAGIC - [ ] Update bronze ingestion notebooks to use dual write
# MAGIC - [ ] Deploy updated notebooks
# MAGIC - [ ] Run job manually to verify dual writes work
# MAGIC
# MAGIC ### Week 2-3: Validation (Days 4-14)
# MAGIC - [ ] Monitor daily: Compare snapshot vs history record counts
# MAGIC - [ ] Check partition sizes (should grow daily)
# MAGIC - [ ] Validate data quality matches between tables
# MAGIC - [ ] Test history queries (last 7 days, specific dates)
# MAGIC - [ ] Monitor storage costs (history tables will grow)
# MAGIC
# MAGIC ### Week 4: Silver Layer (Days 15-21)
# MAGIC - [ ] Create silver `_history` tables
# MAGIC - [ ] Update silver transformation notebooks
# MAGIC - [ ] Validate silver history tables
# MAGIC
# MAGIC ### Week 5-6: Testing (Days 22-35)
# MAGIC - [ ] Update downstream queries to use history tables
# MAGIC - [ ] Test time-travel queries
# MAGIC - [ ] Compare query performance (snapshot vs history with date filters)
# MAGIC - [ ] Update dashboards to query history tables
# MAGIC
# MAGIC ### Week 7: Cutover (Days 36-42)
# MAGIC - [ ] Confirm all queries migrated to history tables
# MAGIC - [ ] Stop writing to snapshot tables (remove from dual_write)
# MAGIC - [ ] Monitor for 7 days
# MAGIC - [ ] Archive or drop snapshot tables
# MAGIC
# MAGIC ### Rollback Plan
# MAGIC If issues arise:
# MAGIC 1. Switch queries back to snapshot tables
# MAGIC 2. Investigate and fix issues
# MAGIC 3. Resume dual writes
# MAGIC 4. Re-validate for another week

# COMMAND ----------

# DBTITLE 1,✅ Update Complete Summary
# MAGIC %md
# MAGIC ## ✅ All Bronze Ingestion Notebooks Updated!
# MAGIC
# MAGIC ### 📝 **Updated Notebooks**
# MAGIC
# MAGIC 1. ✅ **[ingest_fuel.py](#notebook-1251409373489809)** - Fuel prices dual write enabled
# MAGIC 2. ✅ **[ingest_ev.py](#notebook-1211648751446592)** - EV charging stations dual write enabled
# MAGIC 3. ✅ **[ingest_weather.py](#notebook-1211648751446594)** - Weather data dual write enabled
# MAGIC 4. ✅ **[ingest_traffic_hazards.py](#notebook-1211648751446593)** - Traffic hazards dual write enabled
# MAGIC
# MAGIC ### 🔧 **What Was Changed**
# MAGIC
# MAGIC Each notebook now has:
# MAGIC * **New cell**: `write_dual_tables()` helper function
# MAGIC * **Updated write logic**: Writes to BOTH snapshot and `_history` tables
# MAGIC * **Automatic metadata**: Adds `ingestion_date`, `ingestion_timestamp_history`, `pipeline_run_id`
# MAGIC * **Date partitioning**: History tables partitioned by `ingestion_date` for efficient queries
# MAGIC
# MAGIC ### 🚀 **Next Steps**
# MAGIC
# MAGIC 1. **Run your job manually** to test the dual write:
# MAGIC    * Job: [NSW EV Intelligence - Daily Data Pipeline](#job-1061240498083971)
# MAGIC    * Verify both snapshot and history tables are updated
# MAGIC
# MAGIC 2. **Monitor for 7-14 days**:
# MAGIC    * Check history tables grow daily
# MAGIC    * Run validation queries (Cell 12 in this notebook)
# MAGIC    * Compare snapshot vs history data quality
# MAGIC
# MAGIC 3. **After validation period**:
# MAGIC    * Update downstream queries to use history tables
# MAGIC    * Test time-travel queries (last 7 days, specific dates)
# MAGIC    * Gradually migrate dashboards
# MAGIC
# MAGIC ### 📊 **Validation Query**
# MAGIC
# MAGIC Run this after each job run:
# MAGIC ```sql
# MAGIC SELECT 
# MAGIC     ingestion_date,
# MAGIC     COUNT(*) as records
# MAGIC FROM mobility_ai.bronze.fuel_raw_history
# MAGIC GROUP BY ingestion_date
# MAGIC ORDER BY ingestion_date DESC
# MAGIC LIMIT 10;
# MAGIC ```

# COMMAND ----------

# DBTITLE 1,✅ Update Complete Summary
# MAGIC %md
# MAGIC ## ✅ All Bronze Ingestion Notebooks Updated!
# MAGIC
# MAGIC ### 📝 **Updated Notebooks**
# MAGIC
# MAGIC 1. ✅ **[ingest_fuel.py](#notebook-1251409373489809)** - Fuel prices dual write enabled
# MAGIC 2. ✅ **[ingest_ev.py](#notebook-1211648751446592)** - EV charging stations dual write enabled
# MAGIC 3. ✅ **[ingest_weather.py](#notebook-1211648751446594)** - Weather data dual write enabled
# MAGIC 4. ✅ **[ingest_traffic_hazards.py](#notebook-1211648751446593)** - Traffic hazards dual write enabled
# MAGIC
# MAGIC ### 🔧 **What Was Changed**
# MAGIC
# MAGIC Each notebook now has:
# MAGIC * **New cell**: `write_dual_tables()` helper function
# MAGIC * **Updated write logic**: Writes to BOTH snapshot and `_history` tables
# MAGIC * **Automatic metadata**: Adds `ingestion_date`, `ingestion_timestamp_history`, `pipeline_run_id`
# MAGIC * **Date partitioning**: History tables partitioned by `ingestion_date` for efficient queries
# MAGIC
# MAGIC ### 🚀 **Next Steps**
# MAGIC
# MAGIC 1. **Run your job manually** to test the dual write:
# MAGIC    * Job: [NSW EV Intelligence - Daily Data Pipeline](#job-1061240498083971)
# MAGIC    * Verify both snapshot and history tables are updated
# MAGIC
# MAGIC 2. **Monitor for 7-14 days**:
# MAGIC    * Check history tables grow daily
# MAGIC    * Run validation queries (Cell 12 in this notebook)
# MAGIC    * Compare snapshot vs history data quality
# MAGIC
# MAGIC 3. **After validation period**:
# MAGIC    * Update downstream queries to use history tables
# MAGIC    * Test time-travel queries (last 7 days, specific dates)
# MAGIC    * Gradually migrate dashboards
# MAGIC
# MAGIC ### 📊 **Validation Query**
# MAGIC
# MAGIC Run this after each job run:
# MAGIC ```sql
# MAGIC SELECT 
# MAGIC     ingestion_date,
# MAGIC     COUNT(*) as records
# MAGIC FROM mobility_ai.bronze.fuel_raw_history
# MAGIC GROUP BY ingestion_date
# MAGIC ORDER BY ingestion_date DESC
# MAGIC LIMIT 10;
# MAGIC ```
