"""Configuration settings for NSW EV Intelligence Platform"""
import os

# ============================================================================
# RAG Configuration
# ============================================================================
INDEX_NAME = os.getenv("INDEX_NAME", "mobility_ai.rag.ev_documents_index")
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "databricks-meta-llama-3-3-70b-instruct")
TOP_K = int(os.getenv("TOP_K", "5"))

# ============================================================================
# Databricks SQL Configuration
# ============================================================================
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST", "").replace("https://", "")
DATABRICKS_HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/your-warehouse-id")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")

# ============================================================================
# Unity Catalog Tables
# ============================================================================
CHARGER_TABLE = "mobility_ai.gold.charger_recommendations_smart"

# ============================================================================
# Default Query Parameters
# ============================================================================
DEFAULT_MAX_DISTANCE_KM = 30.0
DEFAULT_LIMIT_STATIONS = 10