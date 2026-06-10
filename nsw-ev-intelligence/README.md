# NSW EV Intelligence Platform 🚗⚡

> Comprehensive AI-powered platform for electric vehicle intelligence, charging infrastructure discovery, and smart route planning in New South Wales, Australia.

[![Databricks](https://img.shields.io/badge/Databricks-FF3621?style=flat&logo=databricks&logoColor=white)](https://databricks.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Unity Catalog](https://img.shields.io/badge/Unity_Catalog-Enabled-orange?style=flat)](https://docs.databricks.com/data-governance/unity-catalog/)

---

## 🎯 What This Platform Does

The NSW EV Intelligence Platform is a production-ready web application that combines:

* **🔍 Smart Charging Station Discovery** - Find nearest EV charging stations with intelligent recommendations
* **🤖 AI-Powered Chat (RAG)** - Ask natural language questions about NSW EV infrastructure
* **📊 Real-Time Intelligence** - Live traffic hazards, accessibility scores, and smart routing
* **🗺️ Interactive Web UI** - User-friendly interface for station search and AI assistance
* **🔌 REST API** - Programmatic access for integrations

**Live Demo**: `https://ev-7474646723802544.aws.databricksapps.com`

---

## ✨ Key Features

### 🔌 Charging Station Intelligence
* **1,950+ EV charging stations** across NSW with real-time data
* Distance-based search with haversine calculations
* Filter by charger type (AC/DC), operator, postcode
* Smart recommendations considering traffic hazards
* Tier-based ranking (Tier 1: Excellent, Tier 2: Good, etc.)

### 🤖 RAG-Powered AI Chat
* Ask questions in natural language about EV infrastructure
* Powered by **Databricks Vector Search** and **Foundation Models**
* Semantic search over 116 documents (stations + routes)
* LLM: `databricks-meta-llama-3-3-70b-instruct`
* Source attribution for transparency

### 📈 Data Platform Features
* **Medallion Architecture** (Bronze → Silver → Gold)
* **Unity Catalog** for governed data access
* **Delta Lake** for ACID transactions
* **Serverless compute** for auto-scaling
* **1,950 charging stations**, **429 traffic hazards**, **3,286 fuel stations**

---

## 🏗️ Architecture

### Application Structure

```
nsw-ev-intelligence/
├── app.py                      # Flask application entry point (40 lines)
├── requirements.txt            # Python dependencies
├── app.yaml                    # Databricks App configuration
│
├── src/                        # Source code (modular design)
│   ├── routes/                 # Flask route blueprints
│   │   ├── query_routes.py     # /query endpoint
│   │   ├── chat_routes.py      # /chat endpoint (RAG)
│   │   └── health_routes.py    # /health endpoint
│   ├── services/               # Business logic layer
│   │   ├── sql_service.py      # Databricks SQL connections
│   │   ├── rag_service.py      # Vector search + LLM
│   │   └── intelligence_service.py  # Station intelligence
│   ├── config/
│   │   └── settings.py         # Environment configuration
│   └── utils/
│       └── helpers.py          # Shared utilities (haversine, etc.)
│
├── templates/
│   └── index.html              # Web UI (two-tab interface)
│
├── notebooks/                  # Databricks notebooks
│   ├── RAG_Vector_Search_Setup # One-time RAG setup
│   ├── RAG_Chat_Application    # Interactive RAG demo
│   └── README.md               # Notebook documentation
│
├── docs/                       # Documentation
│   ├── API.md                  # REST API reference
│   ├── ARCHITECTURE.md         # System design guide
│   └── DEPLOYMENT.md           # Deployment instructions
│
├── tests/                      # Unit tests (scaffolded)
└── static/                     # Static assets (CSS, JS, images)
```

### Data Architecture

**Catalog**: `mobility_ai`

**Bronze Layer** (Raw Ingestion)
* `bronze.ev_charging_stations_raw` - 1,958 raw records
* `bronze.traffic_hazards_raw` - 431 incidents
* `bronze.fuel_raw` - 10,627 price records
* `bronze.weather_raw` - 20 weather stations

**Silver Layer** (Cleaned & Validated)
* `silver.ev_charging_stations` - 1,950 validated stations
* `silver.traffic_hazards` - 429 active hazards
* `silver.fuel_prices` - 10,627 prices with categorization
* `silver.weather_conditions` - 20 stations

**Gold Layer** (Business Intelligence)
* `gold.regional_infrastructure_metrics` - 9 NSW regions
* `gold.charger_recommendations_nearest` - Top 10 nearest
* `gold.charger_recommendations_gaps` - Infrastructure gaps
* `gold.charger_recommendations_smart` - Real-time recommendations

**RAG Layer** (Vector Search)
* `rag.ev_documents` - 116 text documents for semantic search
* `rag.ev_documents_index` - Vector search index (managed embeddings)

---

## 🚀 Quick Start

### Prerequisites
* Databricks workspace (AWS) with Unity Catalog
* Python 3.10+
* `mobility_ai` catalog created
* RAG vector search index set up (see [notebooks/README.md](notebooks/README.md))

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Key dependencies**:
* `flask` - Web framework
* `databricks-sql-connector` - SQL warehouse connectivity
* `databricks-sdk` - Vector search and LLM APIs
* `flask-cors` - CORS support

### 2. Configure Environment

Create a `.env` file or set environment variables:

```bash
# Databricks connection
DATABRICKS_HOST=your-workspace.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
DATABRICKS_TOKEN=your-personal-access-token

# Unity Catalog
CATALOG_NAME=mobility_ai
SCHEMA_NAME=silver

# Vector Search (RAG)
VECTOR_INDEX_NAME=mobility_ai.rag.ev_documents_index
LLM_ENDPOINT=databricks-meta-llama-3-3-70b-instruct
```

See [src/config/settings.py](src/config/settings.py) for all configuration options.

### 3. Run Locally

```bash
python app.py
```

Visit `http://localhost:5000` to access the web UI.

### 4. Deploy to Databricks Apps

```bash
databricks apps deploy
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment instructions.

---

## 📖 API Endpoints

### Base URL
```
https://ev-7474646723802544.aws.databricksapps.com
```

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Web UI |
| `/health` | GET | Health check |
| `/query` | POST | Find charging stations |
| `/chat` | POST | AI chat (RAG) |

### Example: Find Charging Stations

```bash
curl -X POST https://ev-7474646723802544.aws.databricksapps.com/query \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": -33.8688,
    "longitude": 151.2093,
    "max_distance_km": 30,
    "charger_type": "DC"
  }'
```

### Example: AI Chat

```bash
curl -X POST https://ev-7474646723802544.aws.databricksapps.com/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Where can I find fast charging stations near Sydney CBD?"
  }'
```

**Full API documentation**: [docs/API.md](docs/API.md)

---

## 🤖 RAG (Retrieval-Augmented Generation)

### How It Works

1. **User asks a question** → "Where are Tesla charging stations?"
2. **Vector Search** retrieves relevant documents from the index
3. **LLM** generates an answer using retrieved context
4. **Response** includes answer + source documents

### Setup RAG

Run the setup notebook once:

```python
# Open: notebooks/RAG_Vector_Search_Setup
# This creates:
# - mobility_ai.rag schema
# - ev_documents table (116 documents)
# - Vector search endpoint (nsw-ev-rag-endpoint)
# - Vector search index (ev_documents_index)
```

**Time**: ~10-15 minutes

### Test RAG

```python
# Open: notebooks/RAG_Chat_Application
# Interactive Gradio UI for testing queries
```

**Documentation**: [notebooks/README.md](notebooks/README.md)

---

## 📊 Key Metrics & Insights

### NSW-Wide Infrastructure
* **Total EV Charging Stations**: 1,950
* **Total Fuel Stations**: 3,286
* **EV Infrastructure Ratio**: 37.2%
* **Total Charging Capacity**: 58,973 kW
* **Average Station Capacity**: 30.2 kW

### Regional EV Readiness (Top 3)
1. **Sydney Metro**: 882 stations, 30,890 kW, 94/100 readiness score
2. **Other/Regional**: 562 stations, 11,823 kW, 82/100 score
3. **Hunter (Newcastle)**: 111 stations, 2,622 kW, 67/100 score

### Charging Speed Distribution
* **Rapid (22-150 kW)**: 1,001 stations (51%)
* **Unknown Rating**: 520 stations (27%)
* **Slow (<7 kW)**: 215 stations (11%)
* **Fast (7-22 kW)**: 135 stations (7%)
* **Ultra-Rapid (>150 kW)**: 79 stations (4%)

### Real-Time Conditions
* **Active Traffic Hazards**: 284 (66% of total hazards)
* **Roadwork Events**: 340 (79% of hazards)
* **Chargers with Accessibility Scores**: All stations

---

## 🛠️ Technical Stack

### Platform
* **Databricks** (AWS) - Data platform
* **Unity Catalog** - Data governance
* **Delta Lake** - Storage format
* **Serverless Compute** - Auto-scaling execution

### Application
* **Flask 2.3+** - Web framework
* **Python 3.10+** - Runtime
* **Databricks SQL Connector** - SQL warehouse access
* **Databricks SDK** - Vector search & Foundation Models

### AI/ML
* **Databricks Vector Search** - Semantic search
* **Foundation Model**: `databricks-meta-llama-3-3-70b-instruct`
* **Embeddings**: `databricks-gte-large-en` (1024 dimensions)
* **RAG Architecture** - Retrieval-Augmented Generation

### Frontend
* **HTML5** - Semantic markup
* **CSS3** - Responsive styling
* **Vanilla JavaScript** - No framework dependencies
* **Leaflet.js** (planned) - Interactive maps

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [API.md](docs/API.md) | REST API reference with examples |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design and patterns |
| [notebooks/README.md](notebooks/README.md) | Notebook setup and usage |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Deployment guide (coming soon) |

---

## 🔧 Data Transformations

### EV Charging Stations
* Column standardization (snake_case)
* Charger rating parsing (extract kW values)
* Speed categorization (Slow/Fast/Rapid/Ultra-Rapid)
* Quality flags (`has_valid_location`, `has_valid_rating`)
* Deduplication by station_name + coordinates

### Traffic Hazards
* Timestamp parsing (DD/MM/YYYY format)
* Severity classification (Major/Moderate/Minor)
* Active status filtering
* Composite key handling

### Fuel Prices
* Fuel categorization (Regular, Premium 95/98, Diesel, LPG)
* Price validation (0-500 cents/liter)
* Timestamp handling
* Station aggregation

### Weather Conditions
* Weather categorization (Clear, Cloudy, Rain, Storm, etc.)
* NSW boundary validation
* Metric validations (temperature, humidity)
* Station deduplication

---

## 🎯 Use Cases

### For EV Drivers
* Find nearest charging stations with live traffic data
* Filter by charger type, speed, operator
* Get smart recommendations based on real-time conditions
* Ask natural language questions about infrastructure

### For Fleet Operators
* Optimize routes considering charger availability
* Monitor charging infrastructure across regions
* Plan charging stops for long-distance trips
* Analyze infrastructure gaps

### For Policy Makers
* Identify infrastructure gaps by region/LGA
* Track EV adoption readiness scores
* Monitor charging station distribution
* Plan future infrastructure investments

### For Developers
* REST API for integration with existing systems
* Python client for programmatic access
* RAG chat for building custom interfaces
* Extensible architecture for new features

---

## 🧪 Testing

### Health Check
```bash
curl https://ev-7474646723802544.aws.databricksapps.com/health
```

### Test Query (Sydney CBD)
```bash
curl -X POST https://ev-7474646723802544.aws.databricksapps.com/query \
  -H "Content-Type: application/json" \
  -d '{"latitude": -33.8688, "longitude": 151.2093, "max_distance_km": 10}'
```

### Test Chat
```bash
curl -X POST https://ev-7474646723802544.aws.databricksapps.com/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the nearest charging stations?"}'
```

### Run Unit Tests (Coming Soon)
```bash
pytest tests/
```

---

## 🔒 Security & Governance

* **Unity Catalog** - Fine-grained access control
* **Databricks Apps Auth** - Automatic OAuth integration
* **Environment Variables** - Secrets management
* **CORS** - Configurable cross-origin requests
* **SQL Injection Protection** - Parameterized queries
* **Rate Limiting** (planned) - API throttling

---

## 🚧 Roadmap

### ✅ Completed
* Medallion data pipeline (Bronze/Silver/Gold)
* REST API with Flask
* RAG chat with vector search
* Web UI with two-tab interface
* Smart recommendations engine
* Comprehensive documentation

### 🔄 In Progress
* Map-based UI with Leaflet.js
* Real-time charging station availability
* Trip planning with route optimization

### 📋 Planned
* User authentication and profiles
* Favorite stations and saved routes
* Push notifications for hazards
* Mobile app (iOS/Android)
* Real-time charging price tracking
* Carbon footprint calculator

---

## 🤝 Contributing

### Development Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd nsw-ev-intelligence
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your Databricks credentials
```

5. **Run locally**
```bash
python app.py
```

### Code Style
* Follow PEP 8 for Python code
* Use docstrings for all functions and classes
* Write unit tests for new features
* Update documentation for API changes

### Pull Request Process
1. Create a feature branch
2. Make changes with tests
3. Update documentation
4. Submit PR with clear description
5. Address review feedback

---

## 📞 Support

### Issues & Questions
* Check [docs/](docs/) for documentation
* Review [API.md](docs/API.md) for endpoint details
* See [notebooks/README.md](notebooks/README.md) for RAG setup
* Contact the NSW EV Intelligence Platform team

### Troubleshooting

**Database connection failed**
```python
# Check your credentials in .env or settings.py
# Verify SQL warehouse is running
# Test with: curl <BASE_URL>/health
```

**Vector search not working**
```python
# Run notebooks/RAG_Vector_Search_Setup
# Wait for index to be ONLINE (~10-15 min)
# Verify: w.vector_search_endpoints.get_endpoint('nsw-ev-rag-endpoint')
```

**No results from /query**
```python
# Check latitude/longitude are valid NSW coordinates
# Increase max_distance_km (default 30 km)
# Verify tables exist: SELECT COUNT(*) FROM mobility_ai.silver.ev_charging_stations
```

---

## 📄 License

This project is proprietary and confidential.

---

## 🙏 Acknowledgments

* **NSW Government** - Open data APIs
* **Databricks** - Data platform and AI capabilities
* **Transport for NSW** - Traffic and infrastructure data
* **Open Source Community** - Flask, Python, and dependencies

---

## 📊 Project Stats

* **Lines of Code**: ~5,000+
* **API Endpoints**: 4
* **Data Tables**: 16 (Bronze/Silver/Gold/RAG)
* **Documents Indexed**: 116
* **Charging Stations**: 1,950
* **Traffic Hazards**: 429
* **Fuel Stations**: 3,286

---

**Version**: 1.0.0  
**Last Updated**: June 10, 2026  
**Status**: Production-Ready ✅
