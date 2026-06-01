# Databricks notebook source
# MAGIC %md
# MAGIC # NSW EV Intelligence Platform - Silver Layer Cleaning
# MAGIC 
# MAGIC **Purpose:** Clean, validate, and standardize bronze data into Silver Delta tables
# MAGIC 
# MAGIC **Transformations:**
# MAGIC - Data quality validation
# MAGIC - Deduplication
# MAGIC - Coordinate validation
# MAGIC - Type conversions
# MAGIC - Standardization of text fields
# MAGIC 
# MAGIC **Output:** Silver tables ready for business logic

# COMMAND ----------

import dlt
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window
import re

# COMMAND ----------

# MAGIC %md
# MAGIC ## Helper Functions

# COMMAND ----------

def is_valid_coordinate(lat, lon):
    """
    Check if coordinates are within NSW bounds.
    NSW approximate bounds: Lat -37.5 to -28.0, Lon 141.0 to 154.0
    """
    return (
        (lat.isNotNull()) & (lon.isNotNull()) &
        (lat >= -37.5) & (lat <= -28.0) &
        (lon >= 141.0) & (lon <= 154.0)
    )

def standardize_text(col_name):
    """Standardize text: trim, title case, remove extra spaces"""
    return trim(regexp_replace(initcap(col(col_name)), "\\s+", " "))

def clean_power_rating(power_col):
    """Extract numeric power rating from string or double"""
    return when(
        power_col.isNotNull(),
        regexp_extract(power_col.cast("string"), r"(\d+\.?\d*)", 1).cast("double")
    ).otherwise(None)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver Table: EV Chargers (Cleaned)

# COMMAND ----------

@dlt.table(
    name="silver_ev_chargers",
    comment="Cleaned and validated EV charging station data",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.managed": "true"
    }
)
@dlt.expect_or_drop("valid_coordinates", "is_valid_coords = true")
@dlt.expect_or_drop("valid_station_id", "station_id IS NOT NULL")
@dlt.expect("has_power_rating", "power_kw_clean > 0", fail_on_violation=False)
def silver_ev_chargers():
    """
    Clean and validate EV charger data from bronze layer.
    """
    return (
        dlt.read_stream("bronze_ev_chargers")
        .withColumn("station_name_clean", standardize_text("station_name"))
        .withColumn("address_clean", standardize_text("address"))
        .withColumn("suburb_clean", standardize_text("suburb"))
        .withColumn("operator_clean", standardize_text("operator"))
        
        # Validate coordinates
        .withColumn("is_valid_coords", 
            is_valid_coordinate(col("latitude"), col("longitude")))
        
        # Clean power rating
        .withColumn("power_kw_clean", clean_power_rating(col("power_kw")))
        
        # Standardize charging level
        .withColumn("charging_speed", 
            when(col("power_kw_clean") >= 100, "Fast")
            .when(col("power_kw_clean") >= 50, "Rapid")
            .when(col("power_kw_clean") >= 22, "Medium")
            .otherwise("Slow"))
        
        # Add quality flags
        .withColumn("has_valid_rating", col("power_kw_clean").isNotNull())
        .withColumn("has_complete_address", 
            col("address_clean").isNotNull() & 
            col("suburb_clean").isNotNull())
        
        # Deduplicate based on station_id and coordinates
        .withColumn("row_num", 
            row_number().over(
                Window.partitionBy("station_id", "latitude", "longitude")
                .orderBy(col("ingestion_timestamp").desc())
            ))
        .filter(col("row_num") == 1)
        .drop("row_num")
        
        # Add processing timestamp
        .withColumn("processed_timestamp", current_timestamp())
        .withColumn("silver_layer_version", lit("1.0"))
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver Table: Traffic Hazards (Cleaned)

# COMMAND ----------

@dlt.table(
    name="silver_traffic_hazards",
    comment="Cleaned and validated traffic hazard data",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.managed": "true"
    }
)
@dlt.expect_or_drop("valid_hazard_coords", "is_valid_coords = true")
@dlt.expect_or_drop("valid_hazard_id", "hazard_id IS NOT NULL")
def silver_traffic_hazards():
    """
    Clean and validate traffic hazard data from bronze layer.
    """
    return (
        dlt.read_stream("bronze_traffic_hazards")
        
        # Standardize text fields
        .withColumn("location_clean", standardize_text("location"))
        .withColumn("suburb_clean", standardize_text("suburb"))
        .withColumn("hazard_type_clean", standardize_text("hazard_type"))
        
        # Validate coordinates
        .withColumn("is_valid_coords", 
            is_valid_coordinate(col("latitude"), col("longitude")))
        
        # Parse timestamps
        .withColumn("start_timestamp", 
            to_timestamp(col("start_time"), "yyyy-MM-dd'T'HH:mm:ss"))
        .withColumn("end_timestamp", 
            to_timestamp(col("end_time"), "yyyy-MM-dd'T'HH:mm:ss"))
        
        # Calculate duration
        .withColumn("duration_hours", 
            when(col("end_timestamp").isNotNull(),
                (unix_timestamp("end_timestamp") - unix_timestamp("start_timestamp")) / 3600
            ).otherwise(None))
        
        # Standardize severity
        .withColumn("severity_level",
            when(lower(col("severity")).contains("high"), "High")
            .when(lower(col("severity")).contains("medium"), "Medium")
            .when(lower(col("severity")).contains("low"), "Low")
            .otherwise("Unknown"))
        
        # Add flags
        .withColumn("is_active", 
            col("end_timestamp").isNull() | (col("end_timestamp") > current_timestamp()))
        
        # Deduplicate
        .withColumn("row_num", 
            row_number().over(
                Window.partitionBy("hazard_id")
                .orderBy(col("ingestion_timestamp").desc())
            ))
        .filter(col("row_num") == 1)
        .drop("row_num")
        
        .withColumn("processed_timestamp", current_timestamp())
        .withColumn("silver_layer_version", lit("1.0"))
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver Table: Regional Demographics (Cleaned)

# COMMAND ----------

@dlt.table(
    name="silver_regional_demographics",
    comment="Cleaned regional demographic data for NSW",
    table_properties={
        "quality": "silver"
    }
)
@dlt.expect_or_drop("valid_population", "population > 0")
@dlt.expect("valid_density", "population_density >= 0", fail_on_violation=False)
def silver_regional_demographics():
    """
    Clean and validate regional demographic data.
    """
    return (
        dlt.read("bronze_regional_demographics")
        
        # Standardize text fields
        .withColumn("region_name_clean", standardize_text("region_name"))
        .withColumn("suburb_clean", standardize_text("suburb"))
        
        # Calculate derived metrics
        .withColumn("population_density_calc",
            when(col("area_sq_km") > 0,
                col("population") / col("area_sq_km")
            ).otherwise(None))
        
        # Use calculated density if original is null
        .withColumn("population_density_final",
            coalesce(col("population_density"), col("population_density_calc")))
        
        # Categorize regions by density
        .withColumn("density_category",
            when(col("population_density_final") >= 1000, "Urban")
            .when(col("population_density_final") >= 100, "Suburban")
            .when(col("population_density_final") >= 10, "Rural")
            .otherwise("Remote"))
        
        # Calculate EV infrastructure metrics
        .withColumn("chargers_per_1000_people",
            when(col("population") > 0,
                (col("existing_ev_chargers") * 1000.0) / col("population")
            ).otherwise(0))
        
        # Deduplicate on region identifier
        .withColumn("row_num", 
            row_number().over(
                Window.partitionBy("lga_code")
                .orderBy(col("ingestion_timestamp").desc())
            ))
        .filter(col("row_num") == 1)
        .drop("row_num")
        
        .withColumn("processed_timestamp", current_timestamp())
        .withColumn("silver_layer_version", lit("1.0"))
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver Table: Traffic Volume (Cleaned)

# COMMAND ----------

@dlt.table(
    name="silver_traffic_volume",
    comment="Cleaned historical traffic volume data",
    table_properties={
        "quality": "silver"
    }
)
@dlt.expect_or_drop("valid_count", "vehicle_count >= 0")
@dlt.expect("valid_speed", "avg_speed_kmh BETWEEN 0 AND 200", fail_on_violation=False)
def silver_traffic_volume():
    """
    Clean and validate traffic volume data for forecasting.
    """
    return (
        dlt.read("bronze_traffic_volume")
        
        # Standardize text fields
        .withColumn("location_name_clean", standardize_text("location_name"))
        .withColumn("road_name_clean", standardize_text("road_name"))
        
        # Parse timestamp
        .withColumn("timestamp_parsed", 
            to_timestamp(col("timestamp"), "yyyy-MM-dd HH:mm:ss"))
        
        # Extract time components
        .withColumn("year", year("timestamp_parsed"))
        .withColumn("month", month("timestamp_parsed"))
        .withColumn("day", dayofmonth("timestamp_parsed"))
        .withColumn("hour", hour("timestamp_parsed"))
        .withColumn("day_of_week", dayofweek("timestamp_parsed"))
        .withColumn("week_of_year", weekofyear("timestamp_parsed"))
        
        # Add time-based flags
        .withColumn("is_peak_hour",
            col("hour").isin([7, 8, 9, 17, 18, 19]))
        .withColumn("is_business_hours",
            (col("hour") >= 9) & (col("hour") <= 17))
        
        # Calculate traffic density metric
        .withColumn("traffic_density_score",
            when(col("avg_speed_kmh") < 20, 5)  # Very congested
            .when(col("avg_speed_kmh") < 40, 4)
            .when(col("avg_speed_kmh") < 60, 3)
            .when(col("avg_speed_kmh") < 80, 2)
            .otherwise(1))  # Free flow
        
        # Deduplicate on location and timestamp
        .withColumn("row_num", 
            row_number().over(
                Window.partitionBy("location_id", "timestamp_parsed")
                .orderBy(col("ingestion_timestamp").desc())
            ))
        .filter(col("row_num") == 1)
        .drop("row_num")
        
        .withColumn("processed_timestamp", current_timestamp())
        .withColumn("silver_layer_version", lit("1.0"))
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Summary
# MAGIC 
# MAGIC Silver layer applies:
# MAGIC - ✅ Coordinate validation (NSW bounds)
# MAGIC - ✅ Deduplication by key fields
# MAGIC - ✅ Text standardization (trim, title case)
# MAGIC - ✅ Type conversions and parsing
# MAGIC - ✅ Derived metrics calculation
# MAGIC - ✅ Quality flags for downstream use
# MAGIC 
# MAGIC Data is now ready for Gold layer business logic.
