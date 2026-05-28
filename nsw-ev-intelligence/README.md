# NSW EV Intelligence Platform 🚗⚡

> Comprehensive data platform for electric vehicle intelligence, traffic analysis, and infrastructure optimization in New South Wales, Australia.

## 📊 Project Overview

This platform provides end-to-end data engineering and analytics for NSW's electric vehicle ecosystem, combining:
- **EV Charging Infrastructure** - 1,950+ charging stations across NSW
- **Traffic Conditions** - Real-time hazard monitoring (roadwork, incidents, floods)
- **Fuel Pricing** - 3,286 traditional fuel stations for transition analysis
- **Weather Data** - Environmental conditions affecting EV performance
- **Regional Analytics** - Infrastructure readiness scoring by region
- **Smart Recommendations** - Intelligent charger recommendations considering real-time conditions

## 🏗️ Architecture: Medallion (Bronze → Silver → Gold)

### Bronze Layer (Raw Data Ingestion)
- **Purpose**: Land raw data from external APIs without transformation
- **Tables**: `mobility_ai.bronze.*`
- **Format**: Delta Lake with full schema preservation
- **Sources**:
  - NSW EV Charging Stations API
  - NSW Traffic Hazards API  
  - NSW Fuel Check API
  - Weather Conditions API

### Silver Layer (Cleaned & Validated)
- **Purpose**: Standardize, validate, and enrich data for analysis
- **Tables**: `mobility_ai.silver.*`
- **Transformations**:
  - Column standardization (snake_case)
  - Data type conversions and validations
  - Quality flags and metadata
  - Deduplication logic
  - Categorization and enrichment

### Gold Layer (Business Intelligence)
- **Purpose**: Business-ready analytics and recommendations
- **Tables**: `mobility_ai.gold.*`
- **Outputs**:
  - Regional infrastructure metrics
  - EV readiness scores by region
  - Charger recommendations (nearest, gaps, smart)
  - Infrastructure gap analysis

## 📁 Project Structure

```
nsw-ev-intelligence/
├── databricks/
│   ├── notebooks/
│   │   ├── bronze/          # Raw data ingestion notebooks
│   │   ├── silver/          # Data transformation notebooks
│   │   └── gold/            # Analytics & recommendations
│   ├── jobs/                # Scheduled job definitions
│   └── README.md
├── src/                     # Python source code
│   ├── ingestion/           # Data ingestion modules
│   ├── transformations/     # Transformation logic
│   └── README.md
├── ui/                      # User interface components
├── infra/                   # Infrastructure as code (Terraform)
├── config/                  # Configuration files
├── docs/                    # Additional documentation
└── README.md               # This file
```

## 🗃️ Unity Catalog Structure

**Catalog**: `mobility_ai`

### Bronze Tables
- `bronze.ev_charging_stations_raw` - 1,958 raw charging station records
- `bronze.traffic_hazards_raw` - 431 traffic incidents and roadwork
- `bronze.fuel_raw` - 10,627 fuel price records
- `bronze.weather_raw` - 20 weather observation stations

### Silver Tables
- `silver.ev_charging_stations` - 1,950 validated stations (8 duplicates removed)
- `silver.traffic_hazards` - 429 active hazards with severity classification
- `silver.fuel_prices` - 10,627 prices with fuel categorization
- `silver.weather_conditions` - 20 stations with quality validation

### Gold Tables
- `gold.regional_infrastructure_metrics` - 9 NSW regions with EV readiness scores
- `gold.charger_recommendations_nearest` - Top 10 nearest chargers for 8 key locations
- `gold.charger_recommendations_gaps` - Infrastructure gap analysis by LGA
- `gold.charger_recommendations_smart` - Real-time recommendations with traffic awareness

## 🚀 Quick Start

### Prerequisites
- Databricks workspace with Unity Catalog enabled
- Serverless compute or interactive cluster
- Access to NSW Government APIs (optional for data refresh)

### Running the Pipeline

1. **Bronze Layer**: Ingest raw data
```python
# Run notebooks in databricks/notebooks/bronze/
# - ingest_ev_charging_stations.py
# - ingest_traffic_hazards.py
# - ingest_fuel_prices.py
# - ingest_weather_conditions.py
```

2. **Silver Layer**: Transform and validate
```python
# Run notebooks in databricks/notebooks/silver/
# - transform_ev_charging_stations.py
# - transform_traffic_hazards.py
# - transform_fuel_prices.py
# - transform_weather_conditions.py
```

3. **Gold Layer**: Generate analytics
```python
# Run notebooks in databricks/notebooks/gold/
# - regional_infrastructure_metrics.py
# - charger_recommendation.py
```

## 📈 Key Metrics & Insights

### NSW-Wide Infrastructure
- **Total EV Charging Stations**: 1,950
- **Total Fuel Stations**: 3,286
- **EV Infrastructure Ratio**: 37.2%
- **Total Charging Capacity**: 58,973 kW
- **Average Station Capacity**: 30.2 kW

### Regional EV Readiness (Top 3)
1. **Sydney Metro**: 882 stations, 30,890 kW, 94/100 readiness score
2. **Other/Regional**: 562 stations, 11,823 kW, 82/100 score
3. **Hunter (Newcastle)**: 111 stations, 2,622 kW, 67/100 score

### Infrastructure Gaps Identified
- **Critical Priority LGAs**: Multiple areas identified
- **Western NSW**: Lowest readiness (28/100) with only 10 stations
- **Gap Severity Scoring**: Based on station count, capacity, and rapid charger availability

### Charging Speed Distribution
- **Rapid (22-150 kW)**: 1,001 stations (51%)
- **Unknown Rating**: 520 stations (27%)
- **Slow (<7 kW)**: 215 stations (11%)
- **Fast (7-22 kW)**: 135 stations (7%)
- **Ultra-Rapid (>150 kW)**: 79 stations (4%)

### Real-Time Conditions
- **Active Traffic Hazards**: 284 (66% of total hazards)
- **Roadwork Events**: 340 (79% of hazards)
- **Chargers Affected by Nearby Hazards**: Tracked in smart recommendations

## 🛠️ Technical Stack

- **Platform**: Databricks (AWS)
- **Compute**: Serverless (CPU)
- **Storage**: Delta Lake
- **Catalog**: Unity Catalog
- **Languages**: Python, SQL, Markdown
- **Key Libraries**: PySpark, pandas, requests

## 🔧 Data Transformations

### EV Charging Stations
- **Column Standardization**: Regex-based snake_case conversion
- **Charger Rating Parsing**: Extract numeric kW from "50 kW" strings using `try_cast`
- **Speed Categorization**: Slow/Fast/Rapid/Ultra-Rapid based on power output
- **Quality Flags**: `has_valid_location`, `has_valid_rating`
- **Deduplication**: Window function on station_name + coordinates

### Traffic Hazards
- **Timestamp Parsing**: Convert DD/MM/YYYY format to timestamps
- **Severity Classification**: Major/Moderate/Minor based on impact flags
- **Active Status**: Real-time filtering of current hazards
- **Composite Key**: Handle missing hazard_id with headline+location hash

### Fuel Prices
- **Fuel Categorization**: Regular Unleaded, Premium 95/98, Diesel, LPG
- **Price Validation**: Range checks (0-500 cents/liter)
- **Timestamp Handling**: DD/MM/YYYY HH:mm:ss format parsing
- **Station Aggregation**: Distinct counts to avoid duplicates

### Weather Conditions
- **Weather Categorization**: Clear, Cloudy, Rain, Storm, Snow/Ice, Fog, Windy
- **NSW Boundary Validation**: Lat/lon range checks
- **Metric Validations**: Temperature (-50 to 60°C), Humidity (0-100%)
- **Station Deduplication**: By station_id + timestamp

## 📊 Analytics Capabilities

### Regional Infrastructure Metrics
- **8 NSW Regions** defined by lat/lon boundaries
- **EV Readiness Score** (0-100):
  - Station count: 40% weight
  - Fast charger availability: 30% weight
  - Total capacity: 30% weight
- **State-wide fuel price benchmarks**
- **Infrastructure ratio tracking**

### Charger Recommendations

#### 1. Nearest Charger Finder
- **Haversine distance calculation** (great-circle)
- **Top 10 nearest** for 8 key NSW locations
- Includes distance, speed, operator, address

#### 2. Infrastructure Gap Analysis
- **Gap Severity Score** (0-100):
  - Charger count deficit: 40 points
  - Capacity shortfall: 30 points
  - Rapid charger availability: 30 points
- **Categories**: Critical, High, Moderate, Low
- **LGA-level granularity**

#### 3. Smart Recommendations
- **Accessibility Score**: Considers traffic hazards within 5km
- **Recommendation Score** (0-100):
  - Charger quality: 40% (Ultra-Rapid > Rapid > Fast > Slow)
  - Real-time accessibility: 60%
- **Tiers**: Excellent, Good, Fair, Limited

## 🎯 Use Cases

1. **EV Drivers**: Find nearest, best-rated chargers with live traffic awareness
2. **Fleet Operators**: Optimize routes considering charger availability and capacity
3. **Infrastructure Planners**: Identify critical gaps for new station deployment
4. **Government Policy**: Data-driven decisions on EV transition strategies
5. **Business Intelligence**: Regional EV adoption readiness analysis
6. **Real Estate**: Assess EV infrastructure for property development

## 📝 Data Quality

### Known Limitations
- **Missing Charger Ratings**: 27% of stations lack numeric kW ratings (marked as "AC")
- **Missing Hazard IDs**: 100% of traffic hazards lack unique identifiers
- **Missing Timestamps**: 13% of hazards missing start_time (immediate events)
- **Fuel Location Data**: No lat/lon available; aggregated at state level
- **Weather Coverage**: Limited to 20 observation stations

### Data Freshness
- **Bronze Layer**: Snapshot as of ingestion timestamp
- **Silver/Gold Layers**: Includes `processed_at` timestamps
- **Recommendation Tier**: `generated_at` / `analyzed_at` tracking
- **Suggested Refresh**: Daily for fuel prices, hourly for traffic/weather

## 🔒 Data Governance

- **Catalog**: Unity Catalog with full lineage tracking
- **Access Control**: Managed through Databricks workspace permissions
- **Audit Trail**: Delta Lake time travel enabled (30-day retention)
- **Schema Evolution**: Enabled for all tables
- **Data Classification**: Public NSW Government data sources

## 📚 Additional Documentation

See subdirectory README files for detailed information:
- [databricks/README.md](databricks/README.md) - Databricks artifacts
- [databricks/notebooks/README.md](databricks/notebooks/README.md) - Notebook documentation
- [databricks/notebooks/bronze/README.md](databricks/notebooks/bronze/README.md) - Bronze layer details
- [databricks/notebooks/silver/README.md](databricks/notebooks/silver/README.md) - Silver layer details
- [databricks/notebooks/gold/README.md](databricks/notebooks/gold/README.md) - Gold layer details
- [src/README.md](src/README.md) - Source code documentation
- [config/README.md](config/README.md) - Configuration details
- [docs/README.md](docs/README.md) - Additional resources

## 🤝 Contributing

This is a demonstration project showcasing modern data engineering practices on Databricks.

## 📄 License

Data sourced from NSW Government Open Data Portal.

## 🙏 Acknowledgments

- **Data Sources**: NSW Government Transport and Fuel APIs
- **Platform**: Databricks Lakehouse Platform
- **Storage**: Delta Lake for ACID transactions and time travel
- **Compute**: Serverless for cost-effective processing

---

**Last Updated**: May 2026
**Project Status**: ✅ Production Ready
**Data Coverage**: NSW, Australia