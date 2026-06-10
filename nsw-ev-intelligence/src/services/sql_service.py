"""Databricks SQL connection service"""
from databricks import sql
from src.config.settings import DATABRICKS_HOST, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN

# Module-level connection state
_sql_connection = None
_sql_failed = False

def get_sql_connection():
    """
    Get or create Databricks SQL connection - lazily initialized on first query
    
    Returns:
        Databricks SQL connection object or None if connection fails
    """
    global _sql_connection, _sql_failed
    
    if _sql_failed:
        return None
        
    if _sql_connection is None:
        try:
            print(f"Connecting to: {DATABRICKS_HOST}")
            print(f"HTTP Path: {DATABRICKS_HTTP_PATH}")
            
            _sql_connection = sql.connect(
                server_hostname=DATABRICKS_HOST,
                http_path=DATABRICKS_HTTP_PATH,
                credentials_provider=lambda: DATABRICKS_TOKEN
            )
            print("✓ Databricks SQL connection initialized successfully")
        except Exception as e:
            print(f"⚠ SQL connection failed: {e}")
            _sql_failed = True
            return None
    
    return _sql_connection

def close_sql_connection():
    """Close the SQL connection if it exists"""
    global _sql_connection
    if _sql_connection:
        try:
            _sql_connection.close()
            print("✓ SQL connection closed")
        except Exception as e:
            print(f"⚠ Error closing SQL connection: {e}")
        finally:
            _sql_connection = None
