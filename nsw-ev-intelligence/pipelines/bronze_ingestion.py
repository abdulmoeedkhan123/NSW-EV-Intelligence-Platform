# Databricks notebook source
# MAGIC %md
# MAGIC # NSW EV Intelligence Platform - Bronze Layer Ingestion
# MAGIC 
# MAGIC **Purpose:** Ingest raw data from NSW Transport APIs and file sources into Bronze Delta tables
# MAGIC 
# MAGIC **Data Sources:**
# MAGIC - NSW Transport EV Charging Stations API
# MAGIC - Live Traffic API (Hazards & Incidents)
# MAGIC - Regional demographic data files
# MAGIC - Historical traffic volume data
# MAGIC 
# MAGIC **Output:** Bronze tables with raw, unprocessed data

# COMMAND ----------

import dlt
from pyspark.sql.functions import *
from pyspark.sql.types import *
from datetime import datetime

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Catalog and schema configuration
CATALOG = "mobility_ai"
BRONZE_SCHEMA = "bronze"

# File paths for batch ingestion (using Volumes)
RAW_FILES_PATH = "/Volumes/mobility_ai/bronze/raw_files"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze Table: EV Charger Stations (Streaming)

# COMMAND ----------

@dlt.table(
    name="bronze_ev_chargers",
    comment="Raw EV charging station data from NSW Transport API",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true"
    }
)
def bronze_ev_chargers():
    """
    Ingest EV charger station data from NSW Transport API.
    Uses Auto Loader for incremental processing.
    """
    schema = StructType([
        StructField("station_id", StringType(), True),
        StructField("station_name", StringType(), True),
        StructField("address", StringType(), True),
        StructField("suburb", StringType(), True),
        StructField("postcode", StringType(), True),
        StructField("latitude", DoubleType(), True),
        StructField("longitude", DoubleType(), True),
        StructField("operator", StringType(), True),
        StructField("charging_level", StringType(), True),
        StructField("connector_type", StringType(), True),
        StructField("power_kw", DoubleType(), True),
        StructField("status", StringType(), True),
        StructField("pricing", StringType(), True),
        StructField("hours_of_operation", StringType(), True),
        StructField("access_type", StringType(), True),
    ])
    
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", f"{RAW_FILES_PATH}/schemas/ev_chargers")
        .option("cloudFiles.inferColumnTypes", "true")
        .schema(schema)
        .load(f"{RAW_FILES_PATH}/ev_chargers/")
        .withColumn("ingestion_timestamp", current_timestamp())
        .withColumn("source", lit("nsw_transport_api"))
        .withColumn("ingestion_date", current_date())
        .withColumn("file_name", input_file_name())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze Table: Traffic Hazards (Streaming)

# COMMAND ----------

@dlt.table(
    name="bronze_traffic_hazards",
    comment="Raw traffic hazard and incident data from Live Traffic API",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true"
    }
)
def bronze_traffic_hazards():
    """
    Ingest traffic hazard data including accidents, roadworks, and incidents.
    """
    schema = StructType([
        StructField("hazard_id", StringType(), True),
        StructField("hazard_type", StringType(), True),
        StructField("severity", StringType(), True),
        StructField("location", StringType(), True),
        StructField("suburb", StringType(), True),
        StructField("latitude", DoubleType(), True),
        StructField("longitude", DoubleType(), True),
        StructField("description", StringType(), True),
        StructField("start_time", StringType(), True),
        StructField("end_time", StringType(), True),
        StructField("impact_level", StringType(), True),
        StructField("affected_roads", StringType(), True),
        StructField("advice", StringType(), True),
    ])
    
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", f"{RAW_FILES_PATH}/schemas/traffic_hazards")
        .option("cloudFiles.inferColumnTypes", "true")
        .schema(schema)
        .load(f"{RAW_FILES_PATH}/traffic_hazards/")
        .withColumn("ingestion_timestamp", current_timestamp())
        .withColumn("source", lit("live_traffic_api"))
        .withColumn("ingestion_date", current_date())
        .withColumn("file_name", input_file_name())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze Table: Regional Demographics (Batch)

# COMMAND ----------

@dlt.table(
    name="bronze_regional_demographics",
    comment="Regional demographic and infrastructure data for NSW",
    table_properties={
        "quality": "bronze"
    }
)
def bronze_regional_demographics():
    """
    Load regional demographic data including population, area, and infrastructure metrics.
    Batch data that updates less frequently.
    """
    schema = StructType([
        StructField("region_name", StringType(), True),
        StructField("lga_code", StringType(), True),
        StructField("suburb", StringType(), True),
        StructField("population", IntegerType(), True),
        StructField("area_sq_km", DoubleType(), True),
        StructField("population_density", DoubleType(), True),
        StructField("median_income", IntegerType(), True),
        StructField("ev_adoption_rate", DoubleType(), True),
        StructField("existing_ev_chargers", IntegerType(), True),
        StructField("major_roads_count", IntegerType(), True),
    ])
    
    return (
        spark.read
        .format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .option("cloudFiles.schemaLocation", f"{RAW_FILES_PATH}/schemas/regional_demographics")
        .schema(schema)
        .load(f"{RAW_FILES_PATH}/regional_demographics/")
        .withColumn("ingestion_timestamp", current_timestamp())
        .withColumn("source", lit("regional_data_files"))
        .withColumn("ingestion_date", current_date())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze Table: Traffic Volume (Batch)

# COMMAND ----------

@dlt.table(
    name="bronze_traffic_volume",
    comment="Historical traffic volume data for NSW roads",
    table_properties={
        "quality": "bronze"
    }
)
def bronze_traffic_volume():
    """
    Load historical traffic volume data for forecasting.
    """
    schema = StructType([
        StructField("location_id", StringType(), True),
        StructField("location_name", StringType(), True),
        StructField("road_name", StringType(), True),
        StructField("timestamp", StringType(), True),
        StructField("vehicle_count", IntegerType(), True),
        StructField("avg_speed_kmh", DoubleType(), True),
        StructField("day_of_week", StringType(), True),
        StructField("hour_of_day", IntegerType(), True),
        StructField("is_weekend", BooleanType(), True),
        StructField("is_holiday", BooleanType(), True),
    ])
    
    return (
        spark.read
        .format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .option("cloudFiles.schemaLocation", f"{RAW_FILES_PATH}/schemas/traffic_volume")
        .schema(schema)
        .load(f"{RAW_FILES_PATH}/traffic_volume/")
        .withColumn("ingestion_timestamp", current_timestamp())
        .withColumn("source", lit("traffic_volume_files"))
        .withColumn("ingestion_date", current_date())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Expectations (Bronze Level)
# MAGIC 
# MAGIC Bronze layer validation is minimal - capture everything, drop only critical failures.

# COMMAND ----------

# No strict quality rules at bronze - we want to capture all data
# Validation happens in silver layer
