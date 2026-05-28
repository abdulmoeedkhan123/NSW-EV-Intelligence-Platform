# NSW EV Intelligence Platform

Comprehensive data platform for electric vehicle intelligence, traffic analysis, and infrastructure optimization in New South Wales.

## 📁 Project Structure

```
nsw-ev-intelligence/
│
├── databricks/          # Databricks-specific assets
│   ├── notebooks/       # Data processing notebooks (Bronze/Silver/Gold)
│   ├── jobs/           # Job definitions and workflows
│   ├── feature_store/  # Feature engineering pipelines
│   └── ml/             # Machine learning models
│
├── src/                # Source code
│   ├── ingestion/      # Data ingestion pipelines
│   ├── transformations/ # Data transformation logic
│   ├── models/         # Data models and schemas
│   ├── ai/             # AI/ML utilities
│   ├── tools/          # Helper tools and utilities
│   └── apis/           # API integrations
│
├── ui/                 # User interface components
│
├── infra/             # Infrastructure as code
│   ├── terraform/     # Terraform configurations
│   └── docker/        # Docker files
│
├── config/            # Configuration files
│
└── docs/              # Documentation
```

## 🎯 Purpose

This platform provides:
* **EV Data Intelligence** - Registration, charging patterns, and usage analytics
* **Traffic Analysis** - Congestion prediction and route optimization
* **Weather Integration** - Environmental impact on EV performance
* **Smart Recommendations** - Charger placement and trip planning

## 📊 Data Architecture

### Medallion Architecture (Bronze → Silver → Gold)

**Bronze Layer** (Raw Data Ingestion)
* `ingest_ev.py` - EV registration and charging data
* `ingest_traffic.py` - Traffic flow and congestion data
* `ingest_weather.py` - Weather and environmental data

**Silver Layer** (Cleaned & Validated)
* `clean_ev.py` - Data quality, deduplication, standardization
* `clean_traffic.py` - Traffic data normalization
* `clean_weather.py` - Weather data enrichment

**Gold Layer** (Business Intelligence)
* `charger_recommendation.py` - Optimal charger placement analysis
* `congestion_forecast.py` - Traffic congestion prediction
* `trip_intelligence.py` - Smart trip planning and routing

## 🚀 Getting Started

### Prerequisites
* Databricks workspace with Unity Catalog enabled
* Python 3.8+
* Spark 3.x

### Quick Start
1. Clone the repository
2. Configure Unity Catalog schemas (bronze/silver/gold/feature_store)
3. Run bronze layer notebooks to ingest data
4. Execute silver layer for data cleaning
5. Deploy gold layer for business intelligence

## 🔧 Development

### Notebook Development
All notebooks follow a consistent structure:
* Markdown documentation at the top
* Configuration and imports
* Data processing logic
* Data quality checks
* Write to Delta tables

### Testing
Each layer includes data quality validation and schema enforcement.

## 📝 Documentation

Detailed documentation available in the `/docs` folder.

---

**Last Updated:** January 2025
