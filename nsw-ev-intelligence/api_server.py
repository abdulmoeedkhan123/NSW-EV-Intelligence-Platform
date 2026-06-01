"""
NSW EV Intelligence Platform - REST API Server
Flask-based REST API for consumer location intelligence
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType
from datetime import datetime
from math import radians, cos, sin, asin, sqrt
from typing import Dict, List, Optional
import json
import traceback

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for mobile app integration

# Initialize Spark session
spark = SparkSession.builder.getOrCreate()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in kilometers"""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    return c * 6371

haversine_udf = F.udf(haversine_distance, DoubleType())

# ============================================================================
# CORE INTELLIGENCE FUNCTIONS (imported from consumer_location_intelligence)
# ============================================================================

import sys
sys.path.append('/Workspace/Users/moeedk1@gmail.com/NSW-EV-Intelligence-Platform/nsw-ev-intelligence')

# Import core functions from the main intelligence module
from consumer_location_intelligence import (
    get_nearest_charging_stations,
    get_cheap_fuel_options,
    get_congestion_forecast,
    get_trip_intelligence,
    get_consumer_intelligence
)

# ============================================================================
# REST API ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "NSW EV Intelligence API",
        "version": "1.0.0"
    }), 200

@app.route('/api/v1/intelligence', methods=['POST'])
def get_intelligence():
    """
    Main endpoint for comprehensive location intelligence.
    
    POST /api/v1/intelligence
    Body: {
        "lat": float (required),
        "lon": float (required),
        "postcode": string (optional),
        "charger_type": string (optional),
        "fuel_type": string (optional),
        "destination_lat": float (optional),
        "destination_lon": float (optional),
        "trip_distance_km": float (optional),
        "max_distance_km": float (optional, default: 30.0),
        "hour_of_day": int (optional)
    }
    """
    try:
        data = request.get_json()
        
        # Validate required parameters
        if 'lat' not in data or 'lon' not in data:
            return jsonify({"error": "Missing required parameters: lat, lon"}), 400
        
        # Extract parameters
        lat = float(data['lat'])
        lon = float(data['lon'])
        postcode = data.get('postcode')
        charger_type = data.get('charger_type')
        fuel_type = data.get('fuel_type')
        destination_lat = float(data['destination_lat']) if data.get('destination_lat') else None
        destination_lon = float(data['destination_lon']) if data.get('destination_lon') else None
        trip_distance_km = float(data['trip_distance_km']) if data.get('trip_distance_km') else None
        max_distance_km = float(data.get('max_distance_km', 30.0))
        hour_of_day = int(data['hour_of_day']) if data.get('hour_of_day') is not None else None
        
        # Get intelligence
        result = get_consumer_intelligence(
            lat=lat,
            lon=lon,
            postcode=postcode,
            charger_type=charger_type,
            fuel_type=fuel_type,
            destination_lat=destination_lat,
            destination_lon=destination_lon,
            trip_distance_km=trip_distance_km,
            max_distance_km=max_distance_km,
            hour_of_day=hour_of_day
        )
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({"error": f"Invalid parameter format: {str(e)}"}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/api/v1/charging-stations', methods=['POST'])
def get_charging_stations_endpoint():
    """
    Endpoint for charging station queries only.
    
    POST /api/v1/charging-stations
    Body: {
        "lat": float (required),
        "lon": float (required),
        "charger_type": string (optional),
        "max_distance_km": float (optional, default: 50.0),
        "limit": int (optional, default: 10)
    }
    """
    try:
        data = request.get_json()
        
        if 'lat' not in data or 'lon' not in data:
            return jsonify({"error": "Missing required parameters: lat, lon"}), 400
        
        result = get_nearest_charging_stations(
            lat=float(data['lat']),
            lon=float(data['lon']),
            charger_type=data.get('charger_type'),
            max_distance_km=float(data.get('max_distance_km', 50.0)),
            limit=int(data.get('limit', 10))
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/fuel-prices', methods=['POST'])
def get_fuel_prices_endpoint():
    """
    Endpoint for fuel price queries only.
    
    POST /api/v1/fuel-prices
    Body: {
        "lat": float (required),
        "lon": float (required),
        "fuel_type": string (optional),
        "max_distance_km": float (optional, default: 50.0)
    }
    """
    try:
        data = request.get_json()
        
        if 'lat' not in data or 'lon' not in data:
            return jsonify({"error": "Missing required parameters: lat, lon"}), 400
        
        result = get_cheap_fuel_options(
            lat=float(data['lat']),
            lon=float(data['lon']),
            fuel_type=data.get('fuel_type'),
            max_distance_km=float(data.get('max_distance_km', 50.0))
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/congestion', methods=['POST'])
def get_congestion_endpoint():
    """
    Endpoint for congestion forecast queries only.
    
    POST /api/v1/congestion
    Body: {
        "lat": float (required),
        "lon": float (required),
        "max_distance_km": float (optional, default: 30.0),
        "hour_of_day": int (optional)
    }
    """
    try:
        data = request.get_json()
        
        if 'lat' not in data or 'lon' not in data:
            return jsonify({"error": "Missing required parameters: lat, lon"}), 400
        
        result = get_congestion_forecast(
            lat=float(data['lat']),
            lon=float(data['lon']),
            max_distance_km=float(data.get('max_distance_km', 30.0)),
            hour_of_day=int(data['hour_of_day']) if data.get('hour_of_day') is not None else None
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/trip', methods=['POST'])
def get_trip_endpoint():
    """
    Endpoint for trip planning queries only.
    
    POST /api/v1/trip
    Body: {
        "origin_lat": float (required),
        "origin_lon": float (required),
        "destination_lat": float (optional),
        "destination_lon": float (optional),
        "trip_distance_km": float (optional)
    }
    """
    try:
        data = request.get_json()
        
        if 'origin_lat' not in data or 'origin_lon' not in data:
            return jsonify({"error": "Missing required parameters: origin_lat, origin_lon"}), 400
        
        result = get_trip_intelligence(
            origin_lat=float(data['origin_lat']),
            origin_lon=float(data['origin_lon']),
            destination_lat=float(data['destination_lat']) if data.get('destination_lat') else None,
            destination_lon=float(data['destination_lon']) if data.get('destination_lon') else None,
            trip_distance_km=float(data['trip_distance_km']) if data.get('trip_distance_km') else None
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    """API documentation endpoint"""
    return jsonify({
        "service": "NSW EV Intelligence Platform API",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health",
            "comprehensive_intelligence": "POST /api/v1/intelligence",
            "charging_stations": "POST /api/v1/charging-stations",
            "fuel_prices": "POST /api/v1/fuel-prices",
            "congestion": "POST /api/v1/congestion",
            "trip_planning": "POST /api/v1/trip"
        },
        "documentation": "https://github.com/yourusername/nsw-ev-intelligence"
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)