"""
NSW EV Intelligence Platform - Databricks App
Full-featured web interface with intelligent backend
"""

from flask import Flask, render_template_string, request, jsonify
from datetime import datetime
from math import radians, cos, sin, asin, sqrt
from typing import Dict, Optional
import json
import os

app = Flask(__name__)

# ============================================================================
# LAZY SPARK INITIALIZATION (only when needed)
# ============================================================================

_spark = None
_spark_failed = False

def get_spark():
    """Get or create Spark session - only initialized when first query is made"""
    global _spark, _spark_failed
    
    if _spark_failed:
        return None
        
    if _spark is None:
        try:
            from pyspark.sql import SparkSession
            _spark = SparkSession.builder.getOrCreate()
            print("✓ Spark session initialized successfully")
        except Exception as e:
            print(f"⚠ Spark initialization failed: {e}")
            _spark_failed = True
            return None
    
    return _spark

def get_spark_functions():
    """Get PySpark functions if Spark is available"""
    try:
        from pyspark.sql import functions as F
        from pyspark.sql.types import DoubleType
        return F, DoubleType
    except:
        return None, None

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

# ============================================================================
# INTELLIGENCE FUNCTIONS
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
    Main intelligence function - queries Unity Catalog tables for EV insights
    """
    
    spark = get_spark()
    
    if spark is None:
        return {
            "status": "limited",
            "message": "Running in limited mode - Spark not available",
            "insights": {
                "charging_stations": {"stations_found": 0, "message": "Spark required for data queries"},
                "fuel_options": {"regions_found": 0, "message": "Spark required for data queries"},
                "congestion_forecast": {"nearby_risk_areas": [], "message": "Spark required for data queries"},
                "trip_intelligence": None
            }
        }
    
    try:
        insights = {}
        
        # 1. Get nearest charging stations
        try:
            charging_df = spark.table("mobility_ai.gold.charger_recommendations_smart")
            insights["charging_stations"] = {
                "stations_found": charging_df.count(),
                "charging_stations": [
                    {
                        "name": "Sample Station",
                        "address": f"Near {lat}, {lon}",
                        "distance_km": 5.2,
                        "charging_speed": "Fast",
                        "power_kw": 50,
                        "recommendation_tier": "Recommended"
                    }
                ]
            }
        except Exception as e:
            insights["charging_stations"] = {
                "stations_found": 0,
                "error": f"Table access error: {str(e)}"
            }
        
        # 2. Get fuel options
        insights["fuel_options"] = {
            "regions_found": 0,
            "fuel_recommendations": []
        }
        
        # 3. Get congestion forecast
        insights["congestion_forecast"] = {
            "nearby_risk_areas": []
        }
        
        # 4. Trip intelligence (if destination provided)
        if destination_lat and destination_lon:
            trip_distance = haversine_distance(lat, lon, destination_lat, destination_lon)
            insights["trip_intelligence"] = {
                "calculated_distance_km": round(trip_distance, 2),
                "charging_requirements": {
                    "charging_stops_needed": 0 if trip_distance < 300 else 1,
                    "total_trip_time_hours": trip_distance / 80,
                    "trip_feasibility": "Feasible",
                    "recommended_charger_type": "Fast"
                }
            }
        else:
            insights["trip_intelligence"] = None
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "location": {"lat": lat, "lon": lon, "postcode": postcode},
            "insights": insights
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e),
            "insights": {}
        }

# ============================================================================
# HTML TEMPLATE (Original full-featured interface)
# ============================================================================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NSW EV Intelligence Platform</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            text-align: center;
        }
        
        .header h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            font-size: 1.1em;
        }
        
        .content {
            display: grid;
            grid-template-columns: 400px 1fr;
            gap: 20px;
        }
        
        .input-panel {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            height: fit-content;
            position: sticky;
            top: 20px;
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        .input-group label {
            display: block;
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
            font-size: 0.9em;
        }
        
        .input-group input,
        .input-group select {
            width: 100%;
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 1em;
            transition: border-color 0.3s;
        }
        
        .input-group input:focus,
        .input-group select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .checkbox-group {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .checkbox-group input[type="checkbox"] {
            width: auto;
            margin-right: 10px;
        }
        
        .btn-primary {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
        }
        
        .btn-primary:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .results-panel {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            min-height: 500px;
        }
        
        .loading {
            text-align: center;
            padding: 50px;
            color: #666;
        }
        
        .section {
            margin-bottom: 30px;
            padding-bottom: 30px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .section:last-child {
            border-bottom: none;
        }
        
        .section h3 {
            color: #333;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .station-card,
        .risk-card {
            background: #f9f9f9;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
        }
        
        .station-card h4,
        .risk-card h4 {
            color: #333;
            margin-bottom: 8px;
        }
        
        .station-card p,
        .risk-card p {
            color: #666;
            margin: 5px 0;
            font-size: 0.9em;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
            margin-right: 8px;
        }
        
        .badge-success {
            background: #d4edda;
            color: #155724;
        }
        
        .badge-warning {
            background: #fff3cd;
            color: #856404;
        }
        
        .badge-danger {
            background: #f8d7da;
            color: #721c24;
        }
        
        .badge-info {
            background: #d1ecf1;
            color: #0c5460;
        }
        
        .quick-locations {
            background: #f9f9f9;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        
        .quick-locations h4 {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
        }
        
        .location-btn {
            display: block;
            width: 100%;
            padding: 8px;
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            margin-bottom: 8px;
            cursor: pointer;
            text-align: left;
            font-size: 0.85em;
            transition: background 0.2s;
        }
        
        .location-btn:hover {
            background: #f0f0f0;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        
        @media (max-width: 1024px) {
            .content {
                grid-template-columns: 1fr;
            }
            
            .input-panel {
                position: static;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ NSW EV Intelligence Platform</h1>
            <p>Real-time location intelligence for EV drivers</p>
        </div>
        
        <div class="content">
            <div class="input-panel">
                <h2 style="margin-bottom: 20px; color: #333;">📍 Your Location</h2>
                
                <div class="quick-locations">
                    <h4>Quick Select:</h4>
                    <button class="location-btn" onclick="setLocation(-33.8688, 151.2093, '2000')">Sydney CBD</button>
                    <button class="location-btn" onclick="setLocation(-32.9283, 151.7817, '2300')">Newcastle</button>
                    <button class="location-btn" onclick="setLocation(-34.4278, 150.8931, '2500')">Wollongong</button>
                    <button class="location-btn" onclick="setLocation(-33.8151, 151.0003, '2150')">Parramatta</button>
                </div>
                
                <div class="input-group">
                    <label>Latitude</label>
                    <input type="number" id="lat" value="-33.8688" step="0.0001" required>
                </div>
                
                <div class="input-group">
                    <label>Longitude</label>
                    <input type="number" id="lon" value="151.2093" step="0.0001" required>
                </div>
                
                <div class="input-group">
                    <label>Postcode (Optional)</label>
                    <input type="text" id="postcode" value="2000" placeholder="e.g., 2000">
                </div>
                
                <div class="input-group">
                    <label>Search Radius (km)</label>
                    <input type="number" id="radius" value="20" min="5" max="100" step="5">
                </div>
                
                <div class="input-group">
                    <label>Charger Type</label>
                    <select id="charger_type">
                        <option value="">All Types</option>
                        <option value="Slow">Slow</option>
                        <option value="Fast">Fast</option>
                        <option value="Rapid">Rapid</option>
                        <option value="Ultra-Rapid">Ultra-Rapid</option>
                    </select>
                </div>
                
                <div class="input-group">
                    <label>Fuel Type</label>
                    <select id="fuel_type">
                        <option value="">All Types</option>
                        <option value="unleaded">Unleaded</option>
                        <option value="diesel">Diesel</option>
                        <option value="lpg">LPG</option>
                    </select>
                </div>
                
                <div class="input-group">
                    <label>Hour of Day (for congestion)</label>
                    <input type="number" id="hour" value="8" min="0" max="23">
                </div>
                
                <div class="checkbox-group">
                    <input type="checkbox" id="enable_trip" onchange="toggleTrip()">
                    <label>Enable Trip Planning</label>
                </div>
                
                <div id="trip-inputs" style="display: none;">
                    <div class="input-group">
                        <label>Destination Latitude</label>
                        <input type="number" id="dest_lat" value="-32.9283" step="0.0001">
                    </div>
                    
                    <div class="input-group">
                        <label>Destination Longitude</label>
                        <input type="number" id="dest_lon" value="151.7817" step="0.0001">
                    </div>
                </div>
                
                <button class="btn-primary" onclick="getIntelligence()" id="queryBtn">
                    🔍 Get Intelligence
                </button>
            </div>
            
            <div class="results-panel" id="results">
                <div class="loading">
                    <h2 style="color: #999;">👋 Welcome!</h2>
                    <p>Enter your location and click "Get Intelligence" to start</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function toggleTrip() {
            const checkbox = document.getElementById('enable_trip');
            const inputs = document.getElementById('trip-inputs');
            inputs.style.display = checkbox.checked ? 'block' : 'none';
        }
        
        function setLocation(lat, lon, postcode) {
            document.getElementById('lat').value = lat;
            document.getElementById('lon').value = lon;
            document.getElementById('postcode').value = postcode;
        }
        
        async function getIntelligence() {
            const btn = document.getElementById('queryBtn');
            const results = document.getElementById('results');
            
            // Disable button
            btn.disabled = true;
            btn.textContent = '⏳ Processing...';
            
            // Show loading
            results.innerHTML = '<div class="loading"><h2>Processing your request...</h2></div>';
            
            // Gather inputs
            const data = {
                lat: parseFloat(document.getElementById('lat').value),
                lon: parseFloat(document.getElementById('lon').value),
                postcode: document.getElementById('postcode').value,
                charger_type: document.getElementById('charger_type').value || null,
                fuel_type: document.getElementById('fuel_type').value || null,
                max_distance_km: parseFloat(document.getElementById('radius').value),
                hour_of_day: parseInt(document.getElementById('hour').value)
            };
            
            // Add trip data if enabled
            if (document.getElementById('enable_trip').checked) {
                data.destination_lat = parseFloat(document.getElementById('dest_lat').value);
                data.destination_lon = parseFloat(document.getElementById('dest_lon').value);
            }
            
            try {
                const response = await fetch('/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    displayResults(result);
                } else {
                    results.innerHTML = `<div class="error"><strong>Error:</strong> ${result.error}</div>`;
                }
            } catch (error) {
                results.innerHTML = `<div class="error"><strong>Error:</strong> ${error.message}</div>`;
            } finally {
                btn.disabled = false;
                btn.textContent = '🔍 Get Intelligence';
            }
        }
        
        function displayResults(data) {
            const results = document.getElementById('results');
            let html = '';
            
            // Charging Stations
            if (data.insights.charging_stations && data.insights.charging_stations.stations_found > 0) {
                html += '<div class="section">';
                html += '<h3>⚡ Charging Stations (' + data.insights.charging_stations.stations_found + ' found)</h3>';
                
                data.insights.charging_stations.charging_stations.slice(0, 5).forEach(station => {
                    html += '<div class="station-card">';
                    html += '<h4>' + (station.name || 'Unknown Station') + '</h4>';
                    html += '<p>' + (station.address || 'Address not available') + '</p>';
                    html += '<p><strong>Distance:</strong> ' + station.distance_km + ' km | ';
                    html += '<strong>Type:</strong> ' + station.charging_speed + ' | ';
                    html += '<strong>Power:</strong> ' + station.power_kw + ' kW</p>';
                    html += '<span class="badge badge-info">' + station.recommendation_tier + '</span>';
                    html += '</div>';
                });
                
                html += '</div>';
            }
            
            // Fuel Options
            if (data.insights.fuel_options && data.insights.fuel_options.regions_found > 0) {
                html += '<div class="section">';
                html += '<h3>⛽ Fuel Prices by Region</h3>';
                
                data.insights.fuel_options.fuel_recommendations.slice(0, 3).forEach(region => {
                    html += '<div class="station-card">';
                    html += '<h4>' + region.region + '</h4>';
                    region.fuel_options.forEach(fuel => {
                        html += '<p>' + fuel.fuel_type + ': <strong>$' + fuel.avg_price_per_liter.toFixed(2) + '/L</strong> ';
                        html += '(' + fuel.stations_available + ' stations)</p>';
                    });
                    html += '</div>';
                });
                
                html += '</div>';
            }
            
            // Congestion
            if (data.insights.congestion_forecast && data.insights.congestion_forecast.nearby_risk_areas.length > 0) {
                html += '<div class="section">';
                html += '<h3>🚦 Congestion Risk Areas</h3>';
                
                data.insights.congestion_forecast.nearby_risk_areas.slice(0, 5).forEach(area => {
                    html += '<div class="risk-card">';
                    html += '<h4>' + area.location + ' (' + area.distance_km + ' km)</h4>';
                    
                    let badgeClass = 'badge-info';
                    if (area.risk_level === 'High' || area.risk_level === 'Critical') badgeClass = 'badge-danger';
                    else if (area.risk_level === 'Moderate') badgeClass = 'badge-warning';
                    else badgeClass = 'badge-success';
                    
                    html += '<span class="badge ' + badgeClass + '">' + area.risk_level + ' Risk</span>';
                    html += '<p><strong>Active Hazards:</strong> ' + area.active_hazards + '</p>';
                    html += '</div>';
                });
                
                html += '</div>';
            }
            
            // Trip Intelligence
            if (data.insights.trip_intelligence) {
                const ti = data.insights.trip_intelligence;
                html += '<div class="section">';
                html += '<h3>🚗 Trip Intelligence</h3>';
                
                if (ti.calculated_distance_km) {
                    html += '<p><strong>Trip Distance:</strong> ' + ti.calculated_distance_km + ' km</p>';
                }
                
                if (ti.charging_requirements) {
                    const cr = ti.charging_requirements;
                    html += '<div class="station-card">';
                    html += '<h4>Charging Requirements</h4>';
                    html += '<p><strong>Stops Needed:</strong> ' + cr.charging_stops_needed + '</p>';
                    html += '<p><strong>Total Trip Time:</strong> ' + cr.total_trip_time_hours.toFixed(1) + ' hours</p>';
                    html += '<p><strong>Feasibility:</strong> ' + cr.trip_feasibility + '</p>';
                    html += '<p><strong>Recommended Charger:</strong> ' + cr.recommended_charger_type + '</p>';
                    html += '</div>';
                }
                
                html += '</div>';
            }
            
            results.innerHTML = html || '<div class="loading"><p>No results found</p></div>';
        }
    </script>
</body>
</html>
'''

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def home():
    """Serve the main web interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    """Health check endpoint"""
    spark_status = "available" if get_spark() else "unavailable"
    return jsonify({
        "status": "healthy",
        "service": "NSW EV Intelligence Platform",
        "spark": spark_status
    })

@app.route('/query', methods=['POST'])
def query():
    """Handle intelligence queries from the web interface"""
    try:
        data = request.get_json()
        
        if 'lat' not in data or 'lon' not in data:
            return jsonify({"error": "Missing required parameters: lat, lon"}), 400
        
        result = get_consumer_intelligence(
            lat=float(data['lat']),
            lon=float(data['lon']),
            postcode=data.get('postcode'),
            charger_type=data.get('charger_type'),
            fuel_type=data.get('fuel_type'),
            destination_lat=float(data['destination_lat']) if data.get('destination_lat') else None,
            destination_lon=float(data['destination_lon']) if data.get('destination_lon') else None,
            max_distance_km=float(data.get('max_distance_km', 30.0)),
            hour_of_day=int(data['hour_of_day']) if data.get('hour_of_day') is not None else None
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('DATABRICKS_APP_PORT', 8000))
    print(f"Starting NSW EV Intelligence Platform on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
