# Databricks Notebooks

Data processing notebooks organized by medallion architecture layers.

## Structure

### Bronze Layer (Raw Ingestion)
- **ingest_ev.py** - EV registration and charging station data
- **ingest_traffic.py** - Traffic flow and congestion data
- **ingest_weather.py** - Weather and environmental data

### Silver Layer (Cleaned Data)
- **clean_ev.py** - Data quality, deduplication, standardization
- **clean_traffic.py** - Traffic data normalization
- **clean_weather.py** - Weather data enrichment

### Gold Layer (Business Intelligence)
- **charger_recommendation.py** - Optimal charger placement analysis
- **congestion_forecast.py** - Traffic congestion prediction models
- **trip_intelligence.py** - Smart trip planning and route optimization

## Usage

Run notebooks in order: Bronze → Silver → Gold
