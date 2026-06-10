# NSW EV Intelligence Platform - Notebooks

This directory contains Databricks notebooks for setup, exploration, and testing of the NSW EV Intelligence Platform.

---

## 📓 Available Notebooks

### 1. **RAG_Vector_Search_Setup**
**Purpose**: One-time setup for RAG (Retrieval-Augmented Generation) functionality

**Location**: `../RAG_Vector_Search_Setup`

**What it does**:
* Creates Unity Catalog schema (`mobility_ai.rag`)
* Prepares document table from EV charging stations and route data
* Creates Vector Search endpoint (`nsw-ev-rag-endpoint`)
* Builds Vector Search index (`mobility_ai.rag.ev_documents_index`) with managed embeddings
* Uses Databricks Foundation Model `databricks-gte-large-en` for embeddings

**When to run**:
* First-time setup of the RAG system
* After adding new EV data sources
* When rebuilding the vector search index

**Prerequisites**:
* Unity Catalog enabled
* `mobility_ai` catalog created
* Source tables available:
  - `mobility_ai.silver.ev_charging_stations`
  - `mobility_ai.gold.trip_routes_optimal`
* Permissions to create schemas, tables, and vector search endpoints

**Steps**:
1. Install dependencies (`databricks-vectorsearch`, `databricks-sdk`)
2. Create RAG schema
3. Prepare document table (converts structured data → text documents)
4. Create Vector Search endpoint
5. Create Delta Sync index with managed embeddings
6. Test vector search queries

**Output**:
* ✅ Schema: `mobility_ai.rag`
* ✅ Table: `mobility_ai.rag.ev_documents` (116 documents)
* ✅ Endpoint: `nsw-ev-rag-endpoint` (Standard, ONLINE)
* ✅ Index: `mobility_ai.rag.ev_documents_index` (ready for queries)

**Estimated Runtime**: 10-15 minutes

---

### 2. **RAG_Chat_Application**
**Purpose**: Interactive RAG chat interface for testing queries

**Location**: `../RAG_Chat_Application`

**What it does**:
* Implements complete RAG pipeline (Retrieve → Prompt → Generate)
* Queries vector search index to find relevant documents
* Uses Databricks Foundation Model `databricks-meta-llama-3-3-70b-instruct` for LLM responses
* Creates Gradio-based chat interface for testing
* Demonstrates prompt engineering for RAG

**When to run**:
* After completing RAG_Vector_Search_Setup
* Testing RAG queries interactively
* Evaluating retrieval quality and LLM responses
* Experimenting with different questions

**Prerequisites**:
* Completed RAG_Vector_Search_Setup notebook
* Vector Search index `mobility_ai.rag.ev_documents_index` is online
* LLM endpoint `databricks-meta-llama-3-3-70b-instruct` is available

**Steps**:
1. Install dependencies (`databricks-vectorsearch`, `databricks-sdk`, `gradio`)
2. Configure index name and LLM endpoint
3. Build retrieval function (queries vector search)
4. Build LLM generation function (calls Foundation Model)
5. Create RAG prompt template
6. Build complete RAG pipeline
7. Launch Gradio chat interface

**Example Questions**:
* "Where can I find fast charging stations near Sydney CBD?"
* "What's the charging speed at Tesla supercharger stations?"
* "Are there any routes with safety hazards or delays?"
* "Find me charging stations operated by NRMA"

**Output**:
* ✅ RAG pipeline functions ready
* ✅ Interactive Gradio chat UI
* ✅ Sample queries tested

**Estimated Runtime**: 5-10 minutes (plus interactive testing time)

---

## 🔧 Notebook Organization

### Current Structure
```
nsw-ev-intelligence/
├── RAG_Vector_Search_Setup          # Setup notebook (in root)
├── RAG_Chat_Application             # Demo notebook (in root)
└── notebooks/                       # Future organized notebooks
    └── README.md                    # This file
```

### Recommended Structure (Future)
```
notebooks/
├── README.md                        # This file
├── 01_vector_search_setup.py       # RAG setup (renamed)
├── 02_rag_chat_demo.py             # RAG chat demo (renamed)
├── 03_data_exploration.py          # EV data analysis (new)
└── 04_model_evaluation.py          # RAG quality metrics (new)
```

**Note**: The notebooks are currently in the project root. Future reorganization will move them here with clearer naming.

---

## 🚀 Getting Started

### First-Time Setup
1. Run **RAG_Vector_Search_Setup** to create the RAG infrastructure
2. Wait for vector index to be online (~10-15 minutes)
3. Run **RAG_Chat_Application** to test the RAG system
4. Use Gradio interface to ask questions

### Regular Usage
* Use the **Databricks App** (`app.py`) for production queries
* Use **RAG_Chat_Application** notebook for testing and experimentation

---

## 📊 Data Flow

### Vector Search Setup Flow
```
EV Charging Stations (silver.ev_charging_stations)
  ↓
Convert to Text Documents
  ↓
mobility_ai.rag.ev_documents (Delta Table with CDC enabled)
  ↓
Vector Search Index (with managed embeddings)
  ↓
nsw-ev-rag-endpoint (ONLINE)
```

### RAG Query Flow
```
User Question
  ↓
Vector Search (retrieve top K documents)
  ↓
Prompt Template (question + context)
  ↓
LLM (databricks-meta-llama-3-3-70b-instruct)
  ↓
AI-Generated Answer + Sources
```

---

## 🧪 Testing & Validation

### Validate Vector Search Setup
```sql
-- Check documents created
SELECT source_table, COUNT(*) as document_count
FROM mobility_ai.rag.ev_documents
GROUP BY source_table;
```

### Test Vector Search Index
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
results = w.vector_search_indexes.query_index(
    index_name="mobility_ai.rag.ev_documents_index",
    columns=["doc_id", "content"],
    query_text="fast charging stations",
    num_results=3
)
```

### Test RAG Pipeline
```python
from src.services.rag_service import rag_pipeline

result = rag_pipeline("Where are Tesla charging stations?")
print(result['answer'])
print(result['sources'])
```

---

## 🔍 Troubleshooting

### Vector Search Index Not Found
```
Error: Index 'mobility_ai.rag.ev_documents_index' not found
```
**Solution**: Run RAG_Vector_Search_Setup notebook to create the index

### Endpoint Offline
```
Error: Endpoint 'nsw-ev-rag-endpoint' is not ONLINE
```
**Solution**: Wait for endpoint to become ONLINE (check status in Vector Search UI)

### LLM Endpoint Not Available
```
Error: Endpoint 'databricks-meta-llama-3-3-70b-instruct' not found
```
**Solution**: 
* Check available endpoints: `w.serving_endpoints.list()`
* Use an alternative model (e.g., `databricks-dbrx-instruct`)
* Update `LLM_ENDPOINT` in notebook configuration

### Empty Retrieval Results
```
Retrieved 0 documents for query: "..."
```
**Solution**:
* Check if documents table has data: `SELECT COUNT(*) FROM mobility_ai.rag.ev_documents`
* Wait for vector index to finish syncing
* Try a different query with more common terms

---

## 📚 Resources

### Databricks Documentation
* [Vector Search Guide](https://docs.databricks.com/en/generative-ai/vector-search.html)
* [Foundation Models API](https://docs.databricks.com/en/machine-learning/foundation-models/index.html)
* [RAG Best Practices](https://docs.databricks.com/en/generative-ai/retrieval-augmented-generation.html)

### Unity Catalog
* [Unity Catalog Overview](https://docs.databricks.com/en/data-governance/unity-catalog/index.html)
* [Delta Change Data Feed](https://docs.databricks.com/en/delta/delta-change-data-feed.html)

---

## 🔄 Maintenance

### Refresh Vector Index (After Data Updates)
The vector search index automatically syncs from the Delta table with Change Data Feed enabled.

**To manually trigger a refresh**:
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
w.vector_search_indexes.sync_index("mobility_ai.rag.ev_documents_index")
```

### Add New Documents
```sql
-- Insert new documents into the Delta table
INSERT INTO mobility_ai.rag.ev_documents (doc_id, content, source_table)
VALUES ('new_doc_id', 'Document content...', 'source_table_name');
```

The vector index will automatically pick up changes via Delta CDC.

---

## 📝 Future Notebooks

### Planned Additions
* **03_data_exploration.py** - EV data analysis and visualization
* **04_model_evaluation.py** - RAG quality metrics and evaluation
* **05_fine_tuning.py** - Custom model fine-tuning on NSW EV data
* **06_batch_inference.py** - Batch RAG queries for analytics

---

## 🤝 Contributing

When adding new notebooks:
1. Use clear, descriptive names (numbered: 01_, 02_, etc.)
2. Add comprehensive markdown documentation
3. Include example outputs
4. Update this README with notebook details
5. Test on a clean environment before committing

---

## 📞 Support

For questions or issues with notebooks:
* Check troubleshooting section above
* Review Databricks documentation
* Contact the NSW EV Intelligence Platform team

---

**Last Updated**: June 10, 2026
