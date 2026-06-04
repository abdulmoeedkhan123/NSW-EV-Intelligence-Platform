"""
NSW EV Intelligence Platform - Databricks App with SQL Connector
Uses Databricks SQL instead of Spark for lighter weight execution
"""

from flask import Flask, render_template_string, request, jsonify
from datetime import datetime
from math import radians, cos, sin, asin, sqrt
from typing import Dict, Optional, List
import json
import os

app = Flask(__name__)

# ============================================================================
# DATABRICKS SQL CONNECTION (replaces Spark)
# ============================================================================

_sql_connection = None
_sql_failed = False

def get_sql_connection():
    """Get or create Databricks SQL connection - only initialized when first query is made"""
    global _sql_connection, _sql_failed
    
    if _sql_failed:
        return None
        
    if _sql_connection is None:
        try:
            from databricks import sql
            
            # Databricks Apps automatically provide these environment variables
            server_hostname = os.getenv("DATABRICKS_HOST", "").replace("https://", "")
            http_path = os.getenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/your-warehouse-id")
            access_token = os.getenv("DATABRICKS_TOKEN")
            
            print(f"Connecting to: {server_hostname}")
            print(f"HTTP Path: {http_path}")
            
            _sql_connection = sql.connect(
                server_hostname=server_hostname,
                http_path=http_path,
                credentials_provider=lambda: access_token
            )
            print("✓ Databricks SQL connection initialized successfully")
        except Exception as e:
            print(f"⚠ SQL connection failed: {e}")
            _sql_failed = True
            return None
    
    return _sql_connection

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in kilometers"""
    if None in [lat1, lon1, lat2, lon2]:
        return None
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    return c * 6371

# ============================================================================
# INTELLIGENCE FUNCTIONS USING SQL
# ============================================================================

def get_consumer_intelligence(
    lat: float,
    lon: float,
    postcode: Optional[str] = None,
    charger_type: Optional[str] = None,
    fuel_type: Optional[str] = None,
    destination_lat: Optional[float] = None,
    destination_lon: Optional[float] = None,
    max_distance_km: float = 30.0,
    hour_of_day: Optional[int] = None
) -> Dict:
    """
    Main intelligence function - queries Unity Catalog tables using SQL
    """
    
    conn = get_sql_connection()
    
    if conn is None:
        return {
            "status": "limited",
            "message": "Running in limited mode - Database connection not available",
            "insights": {
                "charging_stations": {"stations_found": 0, "message": "Database required for queries"},
                "fuel_options": {"regions_found": 0, "message": "Database required for queries"},
                "congestion_forecast": {"nearby_risk_areas": [], "message": "Database required for queries"},
                "trip_intelligence": None
            }
        }
    
    try:
        insights = {}
        
        # ========================================================================
        # 1. Get nearest charging stations using SQL
        # ========================================================================
        try:
            cursor = conn.cursor()
            
            # Build SQL query with Haversine distance calculation
            sql_query = f"""
            WITH station_distances AS (
                SELECT 
                    *,
                    -- Haversine distance calculation in SQL
                    2 * 6371 * ASIN(SQRT(
                        POW(SIN(RADIANS(latitude - {lat}) / 2), 2) +
                        COS(RADIANS({lat})) * COS(RADIANS(latitude)) *
                        POW(SIN(RADIANS(longitude - {lon}) / 2), 2)
                    )) AS distance_km
                FROM mobility_ai.gold.charger_recommendations_smart
                WHERE has_valid_location = TRUE
            )
            SELECT 
                objectid,
                station_name,
                station_address,
                distance_km,
                latitude,
                longitude,
                operator,
                number_of_plugs,
                charger__type,
                charging_speed,
                charger_rating_kw,
                recommendation_tier,
                recommendation_score,
                accessibility_score,
                nearby_hazards_count,
                hazard_types,
                pcode
            FROM station_distances
            WHERE distance_km <= {max_distance_km}
            """
            
            # Add charger type filter if specified
            if charger_type:
                sql_query += f" AND charger__type = '{charger_type}'"
            
            sql_query += " ORDER BY distance_km ASC LIMIT 10"
            
            print(f"Executing SQL query for lat={lat}, lon={lon}")
            cursor.execute(sql_query)
            
            # Fetch results
            charging_stations = []
            for row in cursor.fetchall():
                # Unpack row (cursor returns tuples)
                (objectid, station_name, station_address, distance_km, latitude, longitude,
                 operator, number_of_plugs, charger_type_val, charging_speed, power_kw,
                 recommendation_tier, recommendation_score, accessibility_score,
                 nearby_hazards, hazard_types, pcode) = row
                
                # Use address first part as name if station_name is NULL
                display_name = station_name
                if not display_name and station_address:
                    display_name = station_address.split(',')[0].strip()
                if not display_name:
                    display_name = f"Station {objectid}"
                
                charging_stations.append({
                    "name": display_name,
                    "address": station_address if station_address else "Address not available",
                    "distance_km": round(distance_km, 2),
                    "latitude": latitude,
                    "longitude": longitude,
                    "operator": operator,
                    "number_of_plugs": number_of_plugs,
                    "charger_type": charger_type_val,
                    "charging_speed": charging_speed,
                    "power_kw": power_kw,
                    "recommendation_tier": recommendation_tier,
                    "recommendation_score": recommendation_score,
                    "accessibility_score": accessibility_score,
                    "nearby_hazards": nearby_hazards,
                    "hazard_types": hazard_types if hazard_types else [],
                    "postcode": pcode
                })
            
            cursor.close()
            print(f"Found {len(charging_stations)} charging stations")
            
            insights["charging_stations"] = {
                "stations_found": len(charging_stations),
                "charging_stations": charging_stations,
                "search_radius_km": max_distance_km,
                "user_location": {"lat": lat, "lon": lon}
            }
            
        except Exception as e:
            print(f"Error querying charging stations: {e}")
            insights["charging_stations"] = {
                "stations_found": 0,
                "error": f"Query error: {str(e)}",
                "message": "Could not retrieve charging station data"
            }
        
        # ========================================================================
        # 2. Fuel options (placeholder)
        # ========================================================================
        insights["fuel_options"] = {
            "regions_found": 0,
            "fuel_recommendations": [],
            "message": "Feature coming soon"
        }
        
        # ========================================================================
        # 3. Congestion forecast (placeholder)
        # ========================================================================
        insights["congestion_forecast"] = {
            "nearby_risk_areas": [],
            "message": "Feature coming soon"
        }
        
        # ========================================================================
        # 4. Trip intelligence (placeholder)
        # ========================================================================
        insights["trip_intelligence"] = None
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "insights": insights
        }
        
    except Exception as e:
        print(f"Error in get_consumer_intelligence: {e}")
        return {
            "status": "error",
            "message": f"Intelligence query failed: {str(e)}",
            "insights": {}
        }

# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main web interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    """Health check endpoint"""
    conn = get_sql_connection()
    return jsonify({
        "status": "healthy",
        "database_connected": conn is not None,
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/query', methods=['POST'])
def query_intelligence():
    """Main query endpoint for consumer intelligence"""
    try:
        data = request.get_json()
        
        # Extract parameters
        lat = float(data.get('latitude'))
        lon = float(data.get('longitude'))
        postcode = data.get('postcode')
        charger_type = data.get('charger_type')
        fuel_type = data.get('fuel_type')
        max_distance = float(data.get('max_distance_km', 30.0))
        
        # Optional trip parameters
        dest_lat = data.get('destination_lat')
        dest_lon = data.get('destination_lon')
        if dest_lat: dest_lat = float(dest_lat)
        if dest_lon: dest_lon = float(dest_lon)
        
        hour = data.get('hour_of_day')
        if hour: hour = int(hour)
        
        # Get intelligence
        result = get_consumer_intelligence(
            lat=lat,
            lon=lon,
            postcode=postcode,
            charger_type=charger_type,
            fuel_type=fuel_type,
            destination_lat=dest_lat,
            destination_lon=dest_lon,
            max_distance_km=max_distance,
            hour_of_day=hour
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in /query endpoint: {e}")
        return jsonify({
            "status": "error",
            "message": f"Request processing error: {str(e)}"
        }), 400

# ============================================================================
# HTML TEMPLATE - FIXED TO SHOW ERRORS
# ============================================================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>NSW EV Intelligence Platform</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #667eea;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .form-group {
            display: flex;
            flex-direction: column;
        }
        label {
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
        }
        input, select {
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 40px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
        }
        #results {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            display: none;
        }
        .station-card {
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .error-box {
            background: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            color: #856404;
        }
        .loading {
            text-align: center;
            color: #667eea;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ NSW EV Intelligence Platform</h1>
        <p class="subtitle">Find charging stations near you</p>
        
        <div class="form-grid">
            <div class="form-group">
                <label>Latitude</label>
                <input type="number" id="lat" step="0.0001" value="-33.8688">
            </div>
            <div class="form-group">
                <label>Longitude</label>
                <input type="number" id="lon" step="0.0001" value="151.2093">
            </div>
            <div class="form-group">
                <label>Max Distance (km)</label>
                <input type="number" id="distance" value="30">
            </div>
            <div class="form-group">
                <label>Charger Type</label>
                <select id="charger_type">
                    <option value="">All Types</option>
                    <option value="AC">AC (Standard)</option>
                    <option value="DC">DC (Fast)</option>
                    <option value="Upcoming">Upcoming</option>
                </select>
            </div>
        </div>
        
        <div style="text-align: center;">
            <button onclick="queryIntelligence()">🔍 Get Intelligence</button>
        </div>
        
        <div class="loading" id="loading">⏳ Querying database...</div>
        <div id="results"></div>
    </div>
    
    <script>
        async function queryIntelligence() {
            const loading = document.getElementById('loading');
            const results = document.getElementById('results');
            
            loading.style.display = 'block';
            results.style.display = 'none';
            
            try {
                const response = await fetch('/query', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        latitude: document.getElementById('lat').value,
                        longitude: document.getElementById('lon').value,
                        max_distance_km: document.getElementById('distance').value,
                        charger_type: document.getElementById('charger_type').value
                    })
                });
                
                const data = await response.json();
                displayResults(data);
                
            } catch (error) {
                results.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
                results.style.display = 'block';
            } finally {
                loading.style.display = 'none';
            }
        }
        
        function displayResults(data) {
            const results = document.getElementById('results');
            
            if (data.status === 'error') {
                results.innerHTML = `
                    <div class="error-box">
                        <h3>❌ Error</h3>
                        <p>${data.message}</p>
                    </div>
                `;
                results.style.display = 'block';
                return;
            }
            
            let html = '<h2>📍 Charging Stations Nearby</h2>';
            
            const chargingData = data.insights.charging_stations || {};
            const stations = chargingData.charging_stations || [];
            
            // Check for query error
            if (chargingData.error) {
                html += `
                    <div class="error-box">
                        <h3>⚠️ Database Query Error</h3>
                        <p><strong>Error:</strong> ${chargingData.error}</p>
                        <p><strong>Message:</strong> ${chargingData.message}</p>
                        <p style="margin-top: 10px;">This usually means:</p>
                        <ul style="margin-left: 20px; margin-top: 5px;">
                            <li>Database connection failed</li>
                            <li>App service principal lacks table permissions</li>
                            <li>SQL warehouse is stopped</li>
                        </ul>
                    </div>
                `;
            } else if (stations.length === 0) {
                html += '<p>No charging stations found within the specified radius.</p>';
            } else {
                stations.forEach(station => {
                    html += `
                        <div class="station-card">
                            <h3>${station.name}</h3>
                            <p><strong>📍 ${station.distance_km} km away</strong></p>
                            <p>${station.address}</p>
                            <p>⚡ ${station.charger_type} | ${station.charging_speed} | ${station.power_kw} kW</p>
                            <p>🔌 ${station.number_of_plugs} plugs</p>
                        </div>
                    `;
                });
            }
            
            results.innerHTML = html;
            results.style.display = 'block';
        }
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("Starting NSW EV Intelligence Platform...")
    app.run(host='0.0.0.0', port=8000, debug=False)
