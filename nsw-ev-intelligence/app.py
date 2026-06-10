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

# RAG imports
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

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
# RAG CHAT FUNCTIONALITY
# ============================================================================

# RAG Configuration
INDEX_NAME = "mobility_ai.rag.ev_documents_index"
LLM_ENDPOINT = "databricks-meta-llama-3-3-70b-instruct"
TOP_K = 5

# Initialize Databricks SDK client for RAG
_workspace_client = None

def get_workspace_client():
    """Get or create Databricks Workspace client for RAG"""
    global _workspace_client
    if _workspace_client is None:
        try:
            _workspace_client = WorkspaceClient()
            print("✓ Databricks Workspace client initialized for RAG")
        except Exception as e:
            print(f"⚠ Workspace client initialization failed: {e}")
            return None
    return _workspace_client

def retrieve_relevant_documents(query: str, top_k: int = TOP_K):
    """Retrieve relevant documents from vector search index."""
    w = get_workspace_client()
    if w is None:
        return []
    
    try:
        results = w.vector_search_indexes.query_index(
            index_name=INDEX_NAME,
            columns=["doc_id", "content", "source_table"],
            query_text=query,
            num_results=top_k
        )
        
        documents = []
        if results.result and results.result.data_array:
            for row in results.result.data_array:
                documents.append({
                    "doc_id": row[0],
                    "content": row[1],
                    "source_table": row[2],
                    "score": float(row[-1])
                })
        return documents
    except Exception as e:
        print(f"Error retrieving documents: {e}")
        return []

def generate_response(prompt: str, max_tokens: int = 500):
    """Generate response using Databricks Foundation Models."""
    w = get_workspace_client()
    if w is None:
        return "RAG service is currently unavailable."
    
    try:
        messages = [
            ChatMessage(
                role=ChatMessageRole.SYSTEM,
                content="You are a helpful assistant for the NSW EV Intelligence Platform."
            ),
            ChatMessage(role=ChatMessageRole.USER, content=prompt)
        ]
        
        response = w.serving_endpoints.query(
            name=LLM_ENDPOINT,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.3
        )
        
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content
        return "I'm sorry, I couldn't generate a response."
    except Exception as e:
        return f"Error: {str(e)}"

def create_rag_prompt(question: str, documents: list) -> str:
    """Create RAG prompt combining question with retrieved documents."""
    if not documents:
        return f"""I don't have relevant information. Please ask about:
- EV charging stations in NSW
- Route safety and traffic hazards

Question: {question}"""
    
    context_parts = [f"Document {i} (Score: {doc['score']:.3f}):\n{doc['content']}"
                     for i, doc in enumerate(documents, 1)]
    context = "\n\n".join(context_parts)
    
    return f"""You are an AI assistant for the NSW EV Intelligence Platform. Answer based ONLY on the context below.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

def rag_pipeline(question: str, top_k: int = TOP_K):
    """Complete RAG pipeline: Retrieve → Prompt → Generate."""
    documents = retrieve_relevant_documents(question, top_k=top_k)
    prompt = create_rag_prompt(question, documents)
    answer = generate_response(prompt)
    
    sources = [{"id": doc["doc_id"], "score": doc["score"]}
               for doc in documents]
    
    return {"answer": answer, "sources": sources, "retrieved_docs": documents}

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

@app.route('/chat', methods=['POST'])
def chat():
    """RAG chat endpoint for natural language queries"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({
                "status": "error",
                "message": "Question is required"
            }), 400
        
        # Run RAG pipeline
        result = rag_pipeline(question, top_k=5)
        
        return jsonify({
            "status": "success",
            "answer": result['answer'],
            "sources": result['sources'][:3],  # Return top 3 sources
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"Error in /chat endpoint: {e}")
        return jsonify({
            "status": "error",
            "message": f"Chat processing error: {str(e)}"
        }), 500

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
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }
        .tab {
            padding: 12px 24px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 16px;
            color: #666;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }
        .tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
            font-weight: 600;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
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
        .chat-container {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .chat-messages {
            min-height: 400px;
            max-height: 500px;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .message {
            padding: 12px 16px;
            border-radius: 12px;
            max-width: 80%;
            word-wrap: break-word;
        }
        .message.user {
            align-self: flex-end;
            background: #667eea;
            color: white;
            margin-left: auto;
        }
        .message.assistant {
            align-self: flex-start;
            background: white;
            border: 1px solid #e0e0e0;
        }
        .message .sources {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid rgba(255,255,255,0.3);
            font-size: 0.85em;
        }
        .chat-input-container {
            display: flex;
            gap: 10px;
        }
        .chat-input {
            flex: 1;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
        }
        .example-questions {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 20px;
        }
        .example-btn {
            padding: 8px 16px;
            background: #f0f0f0;
            border: 1px solid #d0d0d0;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.3s;
        }
        .example-btn:hover {
            background: #e0e0e0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ NSW EV Intelligence Platform</h1>
        <p class="subtitle">Find charging stations and get AI-powered insights</p>
        
        <div class="tabs">
            <button class="tab active" onclick="switchTab('stations')">🔍 Find Stations</button>
            <button class="tab" onclick="switchTab('chat')">💬 Ask AI Chat</button>
        </div>
        
        <div id="stations-tab" class="tab-content active">
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
        
        <div id="chat-tab" class="tab-content">
            <div class="chat-container">
                <div class="example-questions">
                    <button class="example-btn" onclick="askExample('Where can I find fast charging stations near Sydney CBD?')">Fast charging near Sydney</button>
                    <button class="example-btn" onclick="askExample('What\'s the charging speed at Tesla supercharger stations?')">Tesla supercharger info</button>
                    <button class="example-btn" onclick="askExample('Are there any routes with safety hazards or delays?')">Route safety</button>
                    <button class="example-btn" onclick="askExample('Find me charging stations operated by NRMA')">NRMA stations</button>
                </div>
                
                <div class="chat-messages" id="chat-messages">
                    <div class="message assistant">
                        <strong>🚗⚡ AI Assistant</strong>
                        <p>Hello! I'm your NSW EV Intelligence assistant. Ask me anything about:</p>
                        <ul>
                            <li>EV charging stations (locations, operators, speeds)</li>
                            <li>Route safety and traffic hazards</li>
                            <li>Trip planning with charging stops</li>
                        </ul>
                    </div>
                </div>
                
                <div class="chat-input-container">
                    <input type="text" id="chat-input" class="chat-input" placeholder="Ask a question about NSW EV infrastructure..." onkeypress="if(event.key==='Enter') sendMessage()">
                    <button onclick="sendMessage()">💬 Send</button>
                    <button onclick="clearChat()" style="background: #e0e0e0; color: #666;">🗑️ Clear</button>
                </div>
            </div>
        </div>
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
        
        // Tab switching
        function switchTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
        }
        
        // Chat functions
        function addMessage(role, content, sources = null) {
            const messagesDiv = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            
            let html = `<strong>${role === 'user' ? 'You' : '🚗⚡ AI Assistant'}</strong>`;
            html += `<p>${content.replace(/\n/g, '<br>')}</p>`;
            
            if (sources && sources.length > 0) {
                html += '<div class="sources"><strong>📚 Sources:</strong><br>';
                sources.forEach((source, i) => {
                    html += `${i + 1}. ${source.id} (relevance: ${source.score.toFixed(2)})<br>`;
                });
                html += '</div>';
            }
            
            messageDiv.innerHTML = html;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        async function sendMessage() {
            const input = document.getElementById('chat-input');
            const question = input.value.trim();
            
            if (!question) return;
            
            // Add user message
            addMessage('user', question);
            input.value = '';
            
            // Add loading indicator
            addMessage('assistant', '⏳ Thinking...');
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ question })
                });
                
                // Remove loading message
                const messagesDiv = document.getElementById('chat-messages');
                messagesDiv.removeChild(messagesDiv.lastChild);
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    addMessage('assistant', data.answer, data.sources);
                } else {
                    addMessage('assistant', `Error: ${data.message}`);
                }
            } catch (error) {
                // Remove loading message
                const messagesDiv = document.getElementById('chat-messages');
                messagesDiv.removeChild(messagesDiv.lastChild);
                addMessage('assistant', `Error: ${error.message}`);
            }
        }
        
        function askExample(question) {
            document.getElementById('chat-input').value = question;
            sendMessage();
        }
        
        function clearChat() {
            const messagesDiv = document.getElementById('chat-messages');
            messagesDiv.innerHTML = `
                <div class="message assistant">
                    <strong>🚗⚡ AI Assistant</strong>
                    <p>Chat cleared! Ask me anything about NSW EV infrastructure.</p>
                </div>
            `;
        }
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("Starting NSW EV Intelligence Platform...")
    app.run(host='0.0.0.0', port=8000, debug=False)
