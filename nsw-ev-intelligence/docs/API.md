# NSW EV Intelligence Platform - API Reference

Complete API documentation for the NSW EV Intelligence Platform REST API.

---

## 📍 Base URL

```
https://ev-7474646723802544.aws.databricksapps.com
```

Replace with your deployed Databricks App URL.

---

## 🔐 Authentication

The API uses **Databricks App authentication**. When deployed as a Databricks App, authentication is handled automatically by the platform.

**For development/testing:**
* No API key required for the deployed app
* Requests are automatically authenticated via Databricks OAuth

---

## 📚 Endpoints Overview

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Web UI (HTML interface) |
| `/health` | GET | Health check and status |
| `/query` | POST | Find EV charging stations |
| `/chat` | POST | RAG-powered AI chat |

---

## 1. Web UI

### GET `/`

Returns the main web interface with two-tab UI (Find Stations + AI Chat).

**Response**: HTML page

**Example**:
```bash
curl https://ev-7474646723802544.aws.databricksapps.com/
```

---

## 2. Health Check

### GET `/health`

Check API health and database connectivity status.

**Response Format**:
```json
{
  "status": "healthy",
  "database_connected": true,
  "timestamp": "2026-06-10T16:30:45.123456"
}
```

**Response Fields**:
* `status` (string): Health status (`"healthy"`)
* `database_connected` (boolean): Whether Databricks SQL connection is active
* `timestamp` (string): ISO 8601 timestamp

**Example Request**:

<details>
<summary><b>cURL</b></summary>

```bash
curl -X GET https://ev-7474646723802544.aws.databricksapps.com/health
```
</details>

<details>
<summary><b>Python</b></summary>

```python
import requests

response = requests.get('https://ev-7474646723802544.aws.databricksapps.com/health')
data = response.json()

print(f"Status: {data['status']}")
print(f"Database Connected: {data['database_connected']}")
```
</details>

<details>
<summary><b>JavaScript</b></summary>

```javascript
fetch('https://ev-7474646723802544.aws.databricksapps.com/health')
  .then(response => response.json())
  .then(data => {
    console.log('Status:', data.status);
    console.log('Database Connected:', data.database_connected);
  });
```
</details>

**Example Response**:
```json
{
  "status": "healthy",
  "database_connected": true,
  "timestamp": "2026-06-10T16:30:45.123456"
}
```

---

## 3. Query Charging Stations

### POST `/query`

Find EV charging stations near a location with smart recommendations.

**Request Body** (JSON):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `latitude` | float | ✅ Yes | User's latitude (-90 to 90) |
| `longitude` | float | ✅ Yes | User's longitude (-180 to 180) |
| `max_distance_km` | float | ❌ No | Search radius in km (default: 30.0) |
| `charger_type` | string | ❌ No | Filter by type: `"AC"`, `"DC"`, `"Upcoming"` |
| `postcode` | string | ❌ No | Postcode filter |
| `fuel_type` | string | ❌ No | Fuel type (future feature) |
| `destination_lat` | float | ❌ No | Trip destination latitude |
| `destination_lon` | float | ❌ No | Trip destination longitude |
| `hour_of_day` | int | ❌ No | Hour for congestion forecast (0-23) |

**Response Format**:
```json
{
  "status": "success",
  "timestamp": "2026-06-10T16:30:45.123456",
  "insights": {
    "charging_stations": {
      "stations_found": 10,
      "search_radius_km": 30.0,
      "user_location": {
        "lat": -33.8688,
        "lon": 151.2093
      },
      "charging_stations": [
        {
          "name": "Sydney CBD Supercharger",
          "address": "123 George St, Sydney NSW 2000",
          "distance_km": 2.5,
          "latitude": -33.8650,
          "longitude": 151.2094,
          "operator": "Tesla Motors",
          "number_of_plugs": 8,
          "charger_type": "DC",
          "charging_speed": "Fast",
          "power_kw": 150,
          "recommendation_tier": "Tier 1",
          "recommendation_score": 0.95,
          "accessibility_score": 0.88,
          "nearby_hazards": 0,
          "hazard_types": [],
          "postcode": "2000"
        }
      ]
    },
    "fuel_options": {
      "regions_found": 0,
      "fuel_recommendations": [],
      "message": "Feature coming soon"
    },
    "congestion_forecast": {
      "nearby_risk_areas": [],
      "message": "Feature coming soon"
    },
    "trip_intelligence": null
  }
}
```

**Station Object Fields**:
* `name` (string): Station name or address
* `address` (string): Full street address
* `distance_km` (float): Distance from user location in kilometers
* `latitude` (float): Station latitude
* `longitude` (float): Station longitude
* `operator` (string): Station operator (e.g., "Tesla Motors", "NRMA")
* `number_of_plugs` (int): Number of charging plugs available
* `charger_type` (string): Charger type (`"AC"`, `"DC"`, `"Upcoming"`)
* `charging_speed` (string): Speed category (`"Fast"`, `"Standard"`, etc.)
* `power_kw` (float): Charging power in kilowatts
* `recommendation_tier` (string): Quality tier (`"Tier 1"`, `"Tier 2"`, etc.)
* `recommendation_score` (float): Overall recommendation score (0-1)
* `accessibility_score` (float): Accessibility score (0-1)
* `nearby_hazards` (int): Number of nearby safety hazards
* `hazard_types` (array): List of hazard types
* `postcode` (string): Postcode/postal code

**Example Requests**:

<details>
<summary><b>cURL</b></summary>

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
</details>

<details>
<summary><b>Python</b></summary>

```python
import requests

url = 'https://ev-7474646723802544.aws.databricksapps.com/query'
payload = {
    'latitude': -33.8688,
    'longitude': 151.2093,
    'max_distance_km': 30,
    'charger_type': 'DC'
}

response = requests.post(url, json=payload)
data = response.json()

if data['status'] == 'success':
    stations = data['insights']['charging_stations']['charging_stations']
    print(f"Found {len(stations)} charging stations")
    
    for station in stations[:3]:  # Show first 3
        print(f"\n{station['name']}")
        print(f"  Distance: {station['distance_km']} km")
        print(f"  Type: {station['charger_type']} - {station['charging_speed']}")
        print(f"  Power: {station['power_kw']} kW")
else:
    print(f"Error: {data.get('message')}")
```
</details>

<details>
<summary><b>JavaScript (Fetch API)</b></summary>

```javascript
const url = 'https://ev-7474646723802544.aws.databricksapps.com/query';
const payload = {
  latitude: -33.8688,
  longitude: 151.2093,
  max_distance_km: 30,
  charger_type: 'DC'
};

fetch(url, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(payload)
})
  .then(response => response.json())
  .then(data => {
    if (data.status === 'success') {
      const stations = data.insights.charging_stations.charging_stations;
      console.log(`Found ${stations.length} charging stations`);
      
      stations.slice(0, 3).forEach(station => {
        console.log(`\n${station.name}`);
        console.log(`  Distance: ${station.distance_km} km`);
        console.log(`  Type: ${station.charger_type} - ${station.charging_speed}`);
      });
    }
  });
```
</details>

**Example Response**:
```json
{
  "status": "success",
  "timestamp": "2026-06-10T16:35:12.456789",
  "insights": {
    "charging_stations": {
      "stations_found": 3,
      "search_radius_km": 30.0,
      "user_location": {
        "lat": -33.8688,
        "lon": 151.2093
      },
      "charging_stations": [
        {
          "name": "Sydney CBD Supercharger",
          "address": "123 George St, Sydney NSW 2000",
          "distance_km": 2.5,
          "latitude": -33.8650,
          "longitude": 151.2094,
          "operator": "Tesla Motors",
          "number_of_plugs": 8,
          "charger_type": "DC",
          "charging_speed": "Fast",
          "power_kw": 150,
          "recommendation_tier": "Tier 1",
          "recommendation_score": 0.95,
          "accessibility_score": 0.88,
          "nearby_hazards": 0,
          "hazard_types": [],
          "postcode": "2000"
        }
      ]
    }
  }
}
```

---

## 4. AI Chat (RAG)

### POST `/chat`

Ask natural language questions about NSW EV infrastructure using RAG (Retrieval-Augmented Generation).

**Request Body** (JSON):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | string | ✅ Yes | Natural language question |

**Response Format**:
```json
{
  "status": "success",
  "answer": "Based on the available data, there are several fast charging stations near Sydney CBD...",
  "sources": [
    {
      "id": "ev_station_123",
      "score": 0.85
    }
  ],
  "timestamp": "2026-06-10T16:40:30.789012"
}
```

**Response Fields**:
* `status` (string): Response status (`"success"` or `"error"`)
* `answer` (string): AI-generated answer based on retrieved documents
* `sources` (array): Top 3 source documents used for the answer
  * `id` (string): Document identifier
  * `score` (float): Relevance score (0-1, higher is more relevant)
* `timestamp` (string): ISO 8601 timestamp

**Example Questions**:
* "Where can I find fast charging stations near Sydney CBD?"
* "What's the charging speed at Tesla supercharger stations?"
* "Are there any routes with safety hazards or delays?"
* "Find me charging stations operated by NRMA"
* "How many DC fast chargers are available in Parramatta?"

**Example Requests**:

<details>
<summary><b>cURL</b></summary>

```bash
curl -X POST https://ev-7474646723802544.aws.databricksapps.com/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Where can I find fast charging stations near Sydney CBD?"
  }'
```
</details>

<details>
<summary><b>Python</b></summary>

```python
import requests

url = 'https://ev-7474646723802544.aws.databricksapps.com/chat'
payload = {
    'question': 'Where can I find fast charging stations near Sydney CBD?'
}

response = requests.post(url, json=payload)
data = response.json()

if data['status'] == 'success':
    print("Answer:", data['answer'])
    print("\nSources:")
    for source in data['sources']:
        print(f"  - {source['id']} (relevance: {source['score']:.2f})")
else:
    print(f"Error: {data.get('message')}")
```
</details>

<details>
<summary><b>JavaScript (Fetch API)</b></summary>

```javascript
const url = 'https://ev-7474646723802544.aws.databricksapps.com/chat';
const payload = {
  question: 'Where can I find fast charging stations near Sydney CBD?'
};

fetch(url, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(payload)
})
  .then(response => response.json())
  .then(data => {
    if (data.status === 'success') {
      console.log('Answer:', data.answer);
      console.log('\nSources:');
      data.sources.forEach(source => {
        console.log(`  - ${source.id} (relevance: ${source.score.toFixed(2)})`);
      });
    }
  });
```
</details>

**Example Response**:
```json
{
  "status": "success",
  "answer": "Based on the available data, there are several fast charging (DC) stations near Sydney CBD. The closest one is the Sydney CBD Supercharger located at 123 George St, which is approximately 2.5 km from the city center. It offers 150 kW fast charging with 8 charging plugs available. Another option is the Tesla Supercharger at Circular Quay, about 1.8 km away, with similar specifications.",
  "sources": [
    {
      "id": "ev_station_123",
      "score": 0.85
    },
    {
      "id": "ev_station_456",
      "score": 0.78
    },
    {
      "id": "ev_station_789",
      "score": 0.72
    }
  ],
  "timestamp": "2026-06-10T16:40:30.789012"
}
```

---

## ⚠️ Error Responses

All endpoints return standard error responses when something goes wrong.

**Error Response Format**:
```json
{
  "status": "error",
  "message": "Human-readable error description"
}
```

**HTTP Status Codes**:

| Code | Meaning | When It Happens |
|------|---------|-----------------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid parameters or missing required fields |
| 500 | Server Error | Internal server error or service unavailable |

**Common Error Scenarios**:

### 1. Missing Required Field
```json
{
  "status": "error",
  "message": "Missing required parameter: latitude"
}
```

### 2. Invalid Parameter Format
```json
{
  "status": "error",
  "message": "Invalid parameter format: latitude must be a number"
}
```

### 3. Database Connection Failed
```json
{
  "status": "limited",
  "message": "Running in limited mode - Database connection not available",
  "insights": {
    "charging_stations": {
      "stations_found": 0,
      "message": "Database required for queries"
    }
  }
}
```

### 4. Empty Question
```json
{
  "status": "error",
  "message": "Question is required"
}
```

### 5. RAG Service Unavailable
```json
{
  "status": "error",
  "message": "Chat processing error: RAG service is currently unavailable"
}
```

---

## 📊 Rate Limiting

**Current Status**: No rate limiting enforced

**Recommended Usage**:
* Batch requests when possible
* Cache responses for repeated queries
* Implement client-side throttling for production apps

---

## 🔍 Query Optimization Tips

### Charging Station Queries
* Use realistic `max_distance_km` values (5-50 km typical)
* Filter by `charger_type` to narrow results
* Sydney CBD coordinates: `-33.8688, 151.2093`
* Parramatta coordinates: `-33.8150, 151.0000`

### AI Chat Queries
* Be specific about locations ("Sydney CBD" vs "Sydney")
* Ask one question at a time
* Include relevant context (e.g., "fast charging" vs just "charging")
* Use follow-up questions to narrow results

---

## 🧪 Testing

### Test Health Endpoint
```bash
curl https://ev-7474646723802544.aws.databricksapps.com/health
```

### Test Query Endpoint (Sydney CBD)
```bash
curl -X POST https://ev-7474646723802544.aws.databricksapps.com/query \
  -H "Content-Type: application/json" \
  -d '{"latitude": -33.8688, "longitude": 151.2093, "max_distance_km": 10}'
```

### Test Chat Endpoint
```bash
curl -X POST https://ev-7474646723802544.aws.databricksapps.com/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the nearest charging stations?"}'
```

---

## 📚 Integration Examples

### Full Python Client Example

```python
import requests
from typing import Dict, List, Optional

class NSWEVClient:
    """Client for NSW EV Intelligence Platform API"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
    
    def health(self) -> Dict:
        """Check API health"""
        response = requests.get(f'{self.base_url}/health')
        response.raise_for_status()
        return response.json()
    
    def find_stations(
        self,
        latitude: float,
        longitude: float,
        max_distance_km: float = 30.0,
        charger_type: Optional[str] = None
    ) -> Dict:
        """Find charging stations near a location"""
        payload = {
            'latitude': latitude,
            'longitude': longitude,
            'max_distance_km': max_distance_km
        }
        if charger_type:
            payload['charger_type'] = charger_type
        
        response = requests.post(f'{self.base_url}/query', json=payload)
        response.raise_for_status()
        return response.json()
    
    def ask_question(self, question: str) -> Dict:
        """Ask a natural language question"""
        payload = {'question': question}
        response = requests.post(f'{self.base_url}/chat', json=payload)
        response.raise_for_status()
        return response.json()

# Usage
client = NSWEVClient('https://ev-7474646723802544.aws.databricksapps.com')

# Check health
health = client.health()
print(f"API Status: {health['status']}")

# Find stations
stations = client.find_stations(-33.8688, 151.2093, charger_type='DC')
print(f"Found {stations['insights']['charging_stations']['stations_found']} stations")

# Ask question
result = client.ask_question('Where are Tesla charging stations?')
print(f"Answer: {result['answer']}")
```

### JavaScript React Example

```javascript
import React, { useState } from 'react';

const API_BASE_URL = 'https://ev-7474646723802544.aws.databricksapps.com';

function EVStationFinder() {
  const [stations, setStations] = useState([]);
  const [loading, setLoading] = useState(false);

  const findStations = async (lat, lon) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          latitude: lat,
          longitude: lon,
          max_distance_km: 30
        })
      });
      
      const data = await response.json();
      if (data.status === 'success') {
        setStations(data.insights.charging_stations.charging_stations);
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={() => findStations(-33.8688, 151.2093)}>
        Find Stations in Sydney
      </button>
      
      {loading && <p>Loading...</p>}
      
      <ul>
        {stations.map(station => (
          <li key={station.name}>
            {station.name} - {station.distance_km} km
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## 🔗 Related Documentation

* [Architecture Guide](./ARCHITECTURE.md) - System design and components
* [Deployment Guide](./DEPLOYMENT.md) - How to deploy the app
* [Notebooks Guide](../notebooks/README.md) - RAG setup and testing

---

## 📞 Support

For API issues or questions:
* Check the [Troubleshooting](#-error-responses) section
* Review error messages and status codes
* Contact the NSW EV Intelligence Platform team

---

**API Version**: 1.0  
**Last Updated**: June 10, 2026
