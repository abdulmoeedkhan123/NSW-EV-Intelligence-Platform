# Databricks notebook source
# MAGIC %md
# MAGIC # NSW EV Intelligence - DLT Pipeline (Parallel Mode)
# MAGIC 
# MAGIC **🔄 Running in PARALLEL with existing notebook-based ETL**
# MAGIC 
# MAGIC **Table Strategy**: All tables use `_dlt` suffix
# MAGIC - Existing: `ev_charging_stations_raw`
# MAGIC - DLT: `ev_charging_stations_raw_dlt`
# MAGIC 
# MAGIC **Source**: Reads from same volume as existing ETL
# MAGIC - Volume: `/Volumes/mobility_ai/bronze/data_upload`
# MAGIC 
# MAGIC **Medallion Architecture**: Bronze → Silver → Gold

# COMMAND ----------

import dlt
from pyspark.sql.functions import *
from pyspark.sql.types import *

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

CATALOG = "mobility_ai"
BRONZE_SCHEMA = "bronze"
SILVER_SCHEMA = "silver"
GOLD_SCHEMA = "gold"

# Existing volume (shared with notebook ETL)
BRONZE_VOLUME_PATH = f"/Volumes/{CATALOG}/{BRONZE_SCHEMA}/data_upload"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🥉 Bronze Layer - Raw Ingestion (DLT)

# COMMAND ----------

@dlt.table(
    name="ev_charging_stations_raw_dlt",
    comment="DLT: Raw EV charging stations (parallel to existing table)",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true",
        "pipeline_mode": "parallel"
    }
)
def ev_charging_stations_raw_dlt():
    return (
        spark.readStream
            .format("cloudFiles")
            .option("cloudFiles.format", "json")
            .option("cloudFiles.inferColumnTypes", "true")
            .option("cloudFiles.schemaLocation", f"{BRONZE_VOLUME_PATH}/_schemas/ev_stations_dlt")
            .load(f"{BRONZE_VOLUME_PATH}/ev_stations/")
            .withColumn("ingestion_timestamp", current_timestamp())
            .withColumn("source_file", input_file_name())
            .withColumn("pipeline_source", lit("dlt"))
    )

# COMMAND ----------

@dlt.table(
    name="traffic_hazards_raw_dlt",
    comment="DLT: Raw traffic hazards - STREAMING (parallel to existing)",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true",
        "pipeline_mode": "parallel"
    }
)
def traffic_hazards_raw_dlt():
    return (
        spark.readStream
            .format("cloudFiles")
            .option("cloudFiles.format", "json")
            .option("cloudFiles.inferColumnTypes", "true")
            .option("cloudFiles.schemaLocation", f"{BRONZE_VOLUME_PATH}/_schemas/traffic_hazards_dlt")
            .load(f"{BRONZE_VOLUME_PATH}/traffic_hazards/")
            .withColumn("ingestion_timestamp", current_timestamp())
            .withColumn("source_file", input_file_name())
            .withColumn("pipeline_source", lit("dlt"))
    )

# COMMAND ----------

@dlt.table(
    name="fuel_raw_dlt",
    comment="DLT: Raw fuel prices (parallel to existing table)",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true",
        "pipeline_mode": "parallel"
    }
)
def fuel_raw_dlt():
    return (
        spark.readStream
            .format("cloudFiles")
            .option("cloudFiles.format", "json")
            .option("cloudFiles.inferColumnTypes", "true")
            .option("cloudFiles.schemaLocation", f"{BRONZE_VOLUME_PATH}/_schemas/fuel_dlt")
            .load(f"{BRONZE_VOLUME_PATH}/fuel/")
            .withColumn("ingestion_timestamp", current_timestamp())
            .withColumn("source_file", input_file_name())
            .withColumn("pipeline_source", lit("dlt"))
    )

# COMMAND ----------

@dlt.table(
    name="weather_raw_dlt",
    comment="DLT: Raw weather data (parallel to existing table)",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true",
        "pipeline_mode": "parallel"
    }
)
def weather_raw_dlt():
    return (
        spark.readStream
            .format("cloudFiles")
            .option("cloudFiles.format", "json")
            .option("cloudFiles.inferColumnTypes", "true")
            .option("cloudFiles.schemaLocation", f"{BRONZE_VOLUME_PATH}/_schemas/weather_dlt")
            .load(f"{BRONZE_VOLUME_PATH}/weather/")
            .withColumn("ingestion_timestamp", current_timestamp())
            .withColumn("source_file", input_file_name())
            .withColumn("pipeline_source", lit("dlt"))
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🥈 Silver Layer - Cleaned & Validated (DLT)

# COMMAND ----------

@dlt.table(
    name="ev_charging_stations_dlt",
    comment="DLT: Cleaned EV charging stations (parallel to existing)",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.managed": "true",
        "delta.enableChangeDataFeed": "true",
        "pipeline_mode": "parallel"
    }
)
@dlt.expect_all_or_drop({
    "valid_latitude": "latitude IS NOT NULL AND latitude BETWEEN -90 AND 90",
    "valid_longitude": "longitude IS NOT NULL AND longitude BETWEEN -180 AND 180",
    "valid_station_id": "station_id IS NOT NULL"
})
def ev_charging_stations_dlt():
    return (
        dlt.read_stream("ev_charging_stations_raw_dlt")
            .withColumnRenamed("StationID", "station_id")
            .withColumnRenamed("OperatorName", "operator_name")
            .withColumnRenamed("AddressLine1", "address_line1")
            .withColumnRenamed("Suburb", "suburb")
            .withColumnRenamed("State", "state")
            .withColumnRenamed("Postcode", "postcode")
            .withColumnRenamed("Latitude", "latitude")
            .withColumnRenamed("Longitude", "longitude")
            .withColumnRenamed("NumberOfPlugs", "number_of_plugs")
            .withColumnRenamed("ChargerType", "charger_type")
            .withColumnRenamed("ChargingPowerKW", "charging_power_kw")
            .withColumn(
                "charging_speed",
                when(col("charging_power_kw") >= 150, "Ultra-Rapid")
                .when(col("charging_power_kw") >= 22, "Rapid")
                .when(col("charging_power_kw") >= 7, "Fast")
                .when(col("charging_power_kw") > 0, "Slow")
                .otherwise("Unknown")
            )
            .withColumn("has_valid_location", 
                (col("latitude").isNotNull()) & (col("longitude").isNotNull()))
            .withColumn("has_valid_rating", col("charging_power_kw").isNotNull())
            .withColumn("processing_timestamp", current_timestamp())
            .withColumn("pipeline_source", lit("dlt"))
            .dropDuplicates(["station_id"])
    )

# COMMAND ----------

@dlt.table(
    name="traffic_hazards_dlt",
    comment="DLT: Cleaned traffic hazards - STREAMING (parallel to existing)",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.managed": "true",
        "delta.enableChangeDataFeed": "true",
        "pipeline_mode": "parallel"
    }
)
@dlt.expect_all_or_drop({
    "valid_hazard": "hazard_id IS NOT NULL OR (headline IS NOT NULL AND location IS NOT NULL)"
})
def traffic_hazards_dlt():
    return (
        dlt.read_stream("traffic_hazards_raw_dlt")
            .withColumn("created_timestamp",
                to_timestamp(col("created"), "dd/MM/yyyy HH:mm:ss"))
            .withColumn("last_updated_timestamp",
                to_timestamp(col("lastUpdated"), "dd/MM/yyyy HH:mm:ss"))
            .withColumn("severity",
                when(col("isMajor") == True, "Major")
                .when(col("isImpactNetwork") == True, "Moderate")
                .otherwise("Minor"))
            .withColumn("is_active",
                when(col("end").isNull(), True)
                .when(to_timestamp(col("end"), "dd/MM/yyyy HH:mm:ss") > current_timestamp(), True)
                .otherwise(False))
            .withColumn("composite_key",
                coalesce(col("hazard_id"), 
                    sha2(concat(col("headline"), col("location")), 256)))
            .withColumn("processing_timestamp", current_timestamp())
            .withColumn("pipeline_source", lit("dlt"))
            .filter(col("is_active") == True)
    )

# COMMAND ----------

@dlt.table(
    name="fuel_prices_dlt",
    comment="DLT: Cleaned fuel prices (parallel to existing)",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.managed": "true",
        "pipeline_mode": "parallel"
    }
)
@dlt.expect_all_or_drop({
    "valid_price": "price BETWEEN 0 AND 500",
    "valid_fuel_type": "fuel_type IS NOT NULL"
})
def fuel_prices_dlt():
    return (
        dlt.read_stream("fuel_raw_dlt")
            .withColumn("fuel_category",
                when(col("fueltype").like("%U91%"), "Regular Unleaded")
                .when(col("fueltype").like("%95%"), "Premium 95")
                .when(col("fueltype").like("%98%"), "Premium 98")
                .when(col("fueltype").like("%Diesel%"), "Diesel")
                .when(col("fueltype").like("%LPG%"), "LPG")
                .otherwise("Other"))
            .withColumn("price_updated_timestamp",
                to_timestamp(col("lastupdated"), "dd/MM/yyyy HH:mm:ss"))
            .withColumn("processing_timestamp", current_timestamp())
            .withColumn("pipeline_source", lit("dlt"))
    )

# COMMAND ----------

@dlt.table(
    name="weather_conditions_dlt",
    comment="DLT: Cleaned weather conditions (parallel to existing)",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.managed": "true",
        "pipeline_mode": "parallel"
    }
)
@dlt.expect_all_or_drop({
    "valid_temperature": "temperature_c BETWEEN -50 AND 60",
    "valid_humidity": "humidity_percent BETWEEN 0 AND 100"
})
def weather_conditions_dlt():
    return (
        dlt.read_stream("weather_raw_dlt")
            .withColumn("weather_category",
                when(col("weather").like("%Clear%"), "Clear")
                .when(col("weather").like("%Cloud%"), "Cloudy")
                .when(col("weather").like("%Rain%"), "Rain")
                .when(col("weather").like("%Storm%"), "Storm")
                .when(col("weather").like("%Snow%"), "Snow/Ice")
                .when(col("weather").like("%Fog%"), "Fog")
                .otherwise("Other"))
            .filter((col("latitude").between(-37.5, -28.0)) &
                   (col("longitude").between(140.0, 154.0)))
            .withColumn("processing_timestamp", current_timestamp())
            .withColumn("pipeline_source", lit("dlt"))
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🥇 Gold Layer - Business Intelligence (DLT)

# COMMAND ----------

@dlt.table(
    name="regional_infrastructure_metrics_dlt",
    comment="DLT: Regional EV infrastructure metrics (parallel to existing)",
    table_properties={
        "quality": "gold",
        "pipelines.autoOptimize.managed": "true",
        "pipeline_mode": "parallel"
    }
)
def regional_infrastructure_metrics_dlt():
    return (
        spark.sql("""
            SELECT
                CASE
                    WHEN latitude BETWEEN -34.1 AND -33.6 AND longitude BETWEEN 150.5 AND 151.5 
                        THEN 'Sydney Metro'
                    WHEN latitude BETWEEN -33.0 AND -32.6 AND longitude BETWEEN 151.5 AND 152.0 
                        THEN 'Hunter (Newcastle)'
                    WHEN latitude BETWEEN -34.5 AND -34.3 AND longitude BETWEEN 150.8 AND 151.0 
                        THEN 'Illawarra (Wollongong)'
                    WHEN latitude BETWEEN -36.5 AND -36.0 AND longitude BETWEEN 146.8 AND 147.5 
                        THEN 'Riverina'
                    WHEN latitude BETWEEN -31.5 AND -30.0 AND longitude BETWEEN 152.5 AND 153.5 
                        THEN 'Mid North Coast'
                    WHEN latitude BETWEEN -29.0 AND -28.0 AND longitude BETWEEN 152.8 AND 153.7 
                        THEN 'Northern Rivers'
                    WHEN latitude BETWEEN -32.0 AND -30.5 AND longitude BETWEEN 148.5 AND 152.0 
                        THEN 'New England'
                    WHEN latitude BETWEEN -34.0 AND -32.0 AND longitude BETWEEN 140.0 AND 148.5 
                        THEN 'Western NSW'
                    ELSE 'Other/Regional'
                END AS region,
                COUNT(DISTINCT station_id) AS total_stations,
                SUM(number_of_plugs) AS total_plugs,
                ROUND(SUM(charging_power_kw), 2) AS total_capacity_kw,
                ROUND(AVG(charging_power_kw), 2) AS avg_capacity_kw,
                COUNT(DISTINCT CASE WHEN charging_speed IN ('Rapid', 'Ultra-Rapid') 
                    THEN station_id END) AS fast_charger_count,
                ROUND(
                    (COUNT(DISTINCT station_id) * 0.4) +
                    (COUNT(DISTINCT CASE WHEN charging_speed IN ('Rapid', 'Ultra-Rapid') 
                        THEN station_id END) * 0.3) +
                    (SUM(charging_power_kw) / 1000 * 0.3), 0
                ) AS ev_readiness_score,
                'dlt' AS pipeline_source,
                current_timestamp() AS calculated_at
            FROM LIVE.ev_charging_stations_dlt
            WHERE has_valid_location = true
            GROUP BY 1
            ORDER BY ev_readiness_score DESC
        """)
    )

# COMMAND ----------

@dlt.table(
    name="charger_recommendations_smart_dlt",
    comment="DLT: Smart charger recommendations (parallel to existing)",
    table_properties={
        "quality": "gold",
        "pipelines.autoOptimize.managed": "true",
        "pipeline_mode": "parallel"
    }
)
def charger_recommendations_smart_dlt():
    return (
        spark.sql("""
            WITH charger_base AS (
                SELECT
                    station_id,
                    operator_name,
                    address_line1,
                    suburb,
                    postcode,
                    latitude,
                    longitude,
                    number_of_plugs,
                    charger_type,
                    charging_power_kw,
                    charging_speed,
                    CASE
                        WHEN charging_speed = 'Ultra-Rapid' THEN 100
                        WHEN charging_speed = 'Rapid' THEN 80
                        WHEN charging_speed = 'Fast' THEN 60
                        WHEN charging_speed = 'Slow' THEN 40
                        ELSE 20
                    END AS charger_quality_score
                FROM LIVE.ev_charging_stations_dlt
                WHERE has_valid_location = true
            ),
            hazard_proximity AS (
                SELECT
                    c.station_id,
                    COUNT(DISTINCT h.composite_key) AS nearby_hazards,
                    CASE
                        WHEN COUNT(DISTINCT h.composite_key) = 0 THEN 100
                        WHEN COUNT(DISTINCT h.composite_key) <= 2 THEN 80
                        WHEN COUNT(DISTINCT h.composite_key) <= 5 THEN 60
                        ELSE 40
                    END AS accessibility_score
                FROM charger_base c
                LEFT JOIN LIVE.traffic_hazards_dlt h
                    ON ABS(c.latitude - h.latitude) < 0.05
                    AND ABS(c.longitude - h.longitude) < 0.05
                    AND h.is_active = true
                GROUP BY c.station_id
            )
            SELECT
                c.*,
                h.nearby_hazards,
                h.accessibility_score,
                ROUND((c.charger_quality_score * 0.4) + (h.accessibility_score * 0.6), 2) 
                    AS recommendation_score,
                CASE
                    WHEN ROUND((c.charger_quality_score * 0.4) + (h.accessibility_score * 0.6), 2) >= 80 
                        THEN 'Tier 1 - Excellent'
                    WHEN ROUND((c.charger_quality_score * 0.4) + (h.accessibility_score * 0.6), 2) >= 60 
                        THEN 'Tier 2 - Good'
                    WHEN ROUND((c.charger_quality_score * 0.4) + (h.accessibility_score * 0.6), 2) >= 40 
                        THEN 'Tier 3 - Fair'
                    ELSE 'Tier 4 - Limited'
                END AS recommendation_tier,
                'dlt' AS pipeline_source,
                current_timestamp() AS calculated_at
            FROM charger_base c
            INNER JOIN hazard_proximity h ON c.station_id = h.station_id
            ORDER BY recommendation_score DESC
        """)
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📊 Pipeline Summary
# MAGIC 
# MAGIC **Tables Created** (all with `_dlt` suffix):
# MAGIC 
# MAGIC **Bronze**: 4 tables (raw ingestion)  
# MAGIC **Silver**: 4 tables (cleaned + validated)  
# MAGIC **Gold**: 2 tables (business intelligence)
# MAGIC 
# MAGIC **Parallel Mode**: Runs alongside existing notebook ETL  
# MAGIC **Source**: Same volume as existing ETL  
# MAGIC **Compare**: Query both versions to validate
