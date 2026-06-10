"""Health check and monitoring routes"""
from flask import Blueprint, jsonify
from datetime import datetime
from src.services.sql_service import get_sql_connection

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint for monitoring app and database status
    
    Returns:
        JSON response with health status and timestamp
    """
    conn = get_sql_connection()
    return jsonify({
        "status": "healthy",
        "database_connected": conn is not None,
        "timestamp": datetime.utcnow().isoformat()
    })
