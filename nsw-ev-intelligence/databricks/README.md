# Databricks Artifacts

This directory contains all Databricks-specific resources for the NSW EV Intelligence Platform.

## 📁 Directory Structure

```
databricks/
├── notebooks/              # PySpark notebooks organized by layer
│   ├── bronze/          # Raw data ingestion (4 notebooks)
│   ├── silver/          # Data transformation (4 notebooks)
│   └── gold/            # Analytics & recommendations (2 notebooks)
├── jobs/                  # Job definitions for scheduling
├── ml/                    # Machine learning models (future)
├── feature_store/         # Feature engineering (future)
└── README.md             # This file
```

## 📓 Notebooks Overview

### Bronze Layer (4 notebooks)
Raw data ingestion from external APIs to Delta Lake tables.

| Notebook | Source API | Target Table | Records |
|----------|------------|--------------|----------|
| `ingest_ev_charging_stations.py` | NSW EV Stations API | `bronze.ev_charging_stations_raw` | 1,958 |
| `ingest_traffic_hazards.py` | NSW Traffic API | `bronze.traffic_hazards_raw` | 431 |
| `ingest_fuel_prices.py` | NSW Fuel Check API | `bronze.fuel_raw` | 10,627 |
| `ingest_weather_conditions.py` | Weather API | `bronze.weather_raw` | 20 |

**Common Pattern**:
1. Fetch JSON data from API
2. Convert to Spark DataFrame
3. Add ingestion metadata (`ingestion_timestamp`)
4. Write to Delta Lake (append or overwrite)

### Silver Layer (4 notebooks)
Cleaned, validated, and enriched data ready for analytics.

| Notebook | Source Table | Target Table | Key Transformations |
|----------|--------------|--------------|---------------------|
| `transform_ev_charging_stations.py` | `bronze.ev_charging_stations_raw` | `silver.ev_charging_stations` | Column standardization, kW parsing, speed categorization, deduplication |
| `transform_traffic_hazards.py` | `bronze.traffic_hazards_raw` | `silver.traffic_hazards` | Timestamp parsing, severity classification, active status, composite keys |
| `transform_fuel_prices.py` | `bronze.fuel_raw` | `silver.fuel_prices` | Fuel categorization, price validation, timestamp parsing |
| `transform_weather_conditions.py` | `bronze.weather_raw` | `silver.weather_conditions` | Weather categorization, NSW bounds validation, metric validation |

**Data Quality Features**:
* Column standardization to snake_case
* Type conversions with `try_cast` for safety
* Data quality flags (e.g., `has_valid_location`)
* Deduplication logic
* Processing timestamps for auditability

### Gold Layer (2 notebooks)
Business-ready analytics and machine learning features.

| Notebook | Purpose | Output Tables | Key Metrics |
|----------|---------|---------------|-------------|
| `regional_infrastructure_metrics.py` | Regional EV readiness analysis | `gold.regional_infrastructure_metrics` | EV readiness scores, station density, capacity by region |
| `charger_recommendation.py` | Intelligent charger recommendations | `gold.charger_recommendations_nearest`<br>`gold.charger_recommendations_gaps`<br>`gold.charger_recommendations_smart` | Nearest chargers, infrastructure gaps, real-time accessibility |

**Analytics Capabilities**:
* Regional segmentation (8 NSW regions)
* EV readiness scoring algorithm
* Haversine distance calculations
* Gap severity analysis by LGA
* Real-time traffic hazard integration

## 🚀 Execution Order

### Full Pipeline (Cold Start)
```python
# 1. Bronze Layer - Ingest all data sources
ingest_ev_charging_stations.py
ingest_traffic_hazards.py
ingest_fuel_prices.py
ingest_weather_conditions.py

# 2. Silver Layer - Transform and validate
transform_ev_charging_stations.py
transform_traffic_hazards.py
transform_fuel_prices.py
transform_weather_conditions.py

# 3. Gold Layer - Generate analytics
regional_infrastructure_metrics.py
charger_recommendation.py
```

### Incremental Updates
```python
# Real-time data (run hourly)
ingest_traffic_hazards.py         # Latest hazards
transform_traffic_hazards.py      # Update silver
charger_recommendation.py         # Refresh smart recommendations

# Daily updates
ingest_fuel_prices.py             # Fuel price changes
transform_fuel_prices.py          # Update silver
regional_infrastructure_metrics.py # Refresh metrics

# Weekly/monthly updates
ingest_ev_charging_stations.py    # New stations
transform_ev_charging_stations.py # Update infrastructure
```

## 🔧 Technical Details

### Compute Requirements
* **Recommended**: Databricks Serverless (CPU)
* **Alternative**: Single-node cluster for development
* **Memory**: 8GB+ recommended for cross-joins in gold layer
* **Runtime**: Databricks Runtime 14.0+ with Unity Catalog

### Key Libraries & Functions
```python
# Core imports used across notebooks
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import DoubleType
import re, math

# Common patterns
F.expr("try_cast(...)")          # Safe type conversions
F.regexp_replace()                # Column standardization
F.to_timestamp(..., "format")    # Timestamp parsing
F.when().when().otherwise()       # Conditional logic
Window.partitionBy().orderBy()    # Deduplication
```

### Data Quality Patterns
```python
# Quality flags
has_valid_location = (lat NOT NULL) AND (lon NOT NULL)
has_valid_rating = (rating NOT NULL) AND (rating > 0)
has_valid_price = (price BETWEEN 0 AND 500)

# Deduplication strategy
Window.partitionBy("key_columns").orderBy("timestamp")
  .withColumn("rank", F.row_number())
  .filter(F.col("rank") == 1)
```

## 📈 Data Volumes & Performance

| Layer | Total Records | Processing Time | Storage (Delta) |
|-------|---------------|-----------------|------------------|
| Bronze | 13,036 | ~2-3 min | ~5 MB |
| Silver | 13,028 | ~3-4 min | ~8 MB |
| Gold | 1,959 (metrics) + 80 (nearest) + 150 (gaps) + 1,950 (smart) | ~5-7 min | ~12 MB |

**Note**: Processing times on Serverless CPU compute.

## 📊 Key Insights Generated

### Regional Metrics
* **Sydney Metro**: Highest EV readiness (94/100)
* **Western NSW**: Critical infrastructure gap (28/100)
* **NSW-wide**: 37.2% EV-to-fuel station ratio

### Charger Recommendations
* **80 recommendations**: Top 10 nearest for 8 key locations
* **150 LGA gaps identified**: Infrastructure deployment priorities
* **1,950 smart recommendations**: Real-time traffic-aware routing

### Traffic Impact
* **284 active hazards**: Affecting charger accessibility
* **5km radius**: Hazard impact zone
* **Accessibility scoring**: Deducts 10 points per nearby hazard

## 🔒 Data Governance

### Unity Catalog Tables
* **Catalog**: `mobility_ai`
* **Schemas**: `bronze`, `silver`, `gold`
* **Access Control**: Workspace-level permissions
* **Lineage**: Full upstream/downstream tracking

### Delta Lake Features
* **ACID Transactions**: Guaranteed consistency
* **Time Travel**: 30-day retention
* **Schema Evolution**: `overwriteSchema` enabled
* **Optimization**: Auto-optimization recommended

## 🔄 Refresh Schedule Recommendations

| Data Source | Refresh Frequency | Reason |
|-------------|-------------------|--------|
| EV Stations | Weekly | Infrastructure changes slowly |
| Traffic Hazards | Hourly | Real-time conditions |
| Fuel Prices | Daily | Price updates daily |
| Weather | Hourly | Current conditions |
| Regional Metrics | Daily | Aggregated stats |
| Recommendations | On-demand | Query-time generation |

## 🛠️ Jobs (Future)

Scheduled jobs for automated pipeline execution:

```
jobs/
├── bronze_ingestion_job.json       # Scheduled data ingestion
├── silver_transformation_job.json  # Data quality processing
└── gold_analytics_job.json         # Business intelligence
```

**Recommended Schedule**:
* Bronze ingestion: `0 */1 * * *` (hourly)
* Silver transformation: `15 */1 * * *` (hourly, 15min offset)
* Gold analytics: `0 0 * * *` (daily at midnight)

## 📝 Notebook Standards

### Structure
1. **Markdown cell**: Overview, business questions, output tables
2. **Configuration cell**: Table paths, constants, parameters
3. **Data loading**: Read source tables with validation
4. **Transformation logic**: Business rules and data quality
5. **Write to target**: Delta Lake with metadata
6. **Validation cell**: Summary statistics and insights

### Print Statement Formatting
* Double-line borders (`═`) for major sections
* Single-line borders (`─`) for subsections
* Emoji prefixes for visual categorization
* Consistent indentation with bullet points (`•`)
* Number formatting with thousands separators

### Error Handling
* Use `try_cast` instead of direct casts
* Add data quality flags for validation
* Include row count checks before/after transforms
* Log processing timestamps

## 📚 Additional Resources

* [Bronze Layer README](notebooks/bronze/README.md) - Data ingestion details
* [Silver Layer README](notebooks/silver/README.md) - Transformation logic
* [Gold Layer README](notebooks/gold/README.md) - Analytics documentation
* [Unity Catalog Docs](https://docs.databricks.com/data-governance/unity-catalog/index.html)
* [Delta Lake Guide](https://docs.databricks.com/delta/index.html)

---

**Last Updated**: May 2026  
**Databricks Runtime**: 14.0+  
**Unity Catalog**: Required