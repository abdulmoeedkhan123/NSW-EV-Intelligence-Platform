# NSW EV Intelligence Platform - API Documentation

## Overview

The NSW EV Intelligence Platform provides real-time, location-based recommendations for EV drivers including:
- **Nearest charging stations** by type and distance
- **Cheap fuel options** for hybrid/ICE vehicles
- **Congestion forecasts** with timing and severity
- **Trip intelligence** with route planning and charging stops

## Architecture

```
Mobile Apps / Web UI
        ↓
   REST API (Flask)
        ↓
   PySpark + Gold Tables
        ↓
mobility_ai.gold schema
```

## Deployment Options

### Option 1: Databricks App (Recommended)

**For Web-based Consumer Interface**

```bash
# Deploy the app
databricks apps create nsw-ev-intelligence-app \
  --source-code-path /Workspace/Users/moeedk1@gmail.com/NSW-EV-Intelligence-Platform/nsw-ev-intelligence/app.py
```

The app will be accessible at: `https://<workspace-url>/apps/nsw-ev-intelligence-app`

### Option 2: REST API Server

**For Mobile App Integration**

```python
# Run the API server
python api_server.py
```

API will be available at: `http://localhost:8000`

### Option 3: Notebook Integration

**For Interactive Use**

Run the `consumer_location_intelligence.py` notebook and use the interactive widgets.

## REST API Endpoints

### Base URL
```
https://<your-databricks-workspace>/apps/nsw-ev-intelligence-app/api/v1
```

### 1. Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-06-01T17:30:00",
  "service": "NSW EV Intelligence API",
  "version": "1.0.0"
}
```

### 2. Comprehensive Intelligence
```http
POST /api/v1/intelligence
Content-Type: application/json
```

**Request Body:**
```json
{
  "lat": -33.8688,
  "lon": 151.2093,
  "postcode": "2000",
  "charger_type": "Fast",
  "fuel_type": "unleaded",
  "destination_lat": -32.9283,
  "destination_lon": 151.7817,
  "max_distance_km": 30.0,
  "hour_of_day": 8
}
```

**Response:**
```json
{
  "query_timestamp": "2026-06-01T17:30:00",
  "user_input": {
    "location": {"lat": -33.8688, "lon": 151.2093},
    "postcode": "2000",
    "search_radius_km": 30.0
  },
  "insights": {
    "charging_stations": {
      "stations_found": 10,
      "charging_stations": []
    },
    "fuel_options": {
      "regions_found": 5,
      "fuel_recommendations": []
    },
    "congestion_forecast": {
      "nearby_risk_areas": []
    },
    "trip_intelligence": {
      "calculated_distance_km": 117.3,
      "charging_requirements": {}
    }
  }
}
```

### 3. Charging Stations Only
```http
POST /api/v1/charging-stations
Content-Type: application/json
```

**Request Body:**
```json
{
  "lat": -33.8688,
  "lon": 151.2093,
  "charger_type": "Fast",
  "max_distance_km": 50.0,
  "limit": 10
}
```

### 4. Fuel Prices Only
```http
POST /api/v1/fuel-prices
Content-Type: application/json
```

**Request Body:**
```json
{
  "lat": -33.8688,
  "lon": 151.2093,
  "fuel_type": "unleaded",
  "max_distance_km": 50.0
}
```

### 5. Congestion Forecast Only
```http
POST /api/v1/congestion
Content-Type: application/json
```

**Request Body:**
```json
{
  "lat": -33.8688,
  "lon": 151.2093,
  "max_distance_km": 30.0,
  "hour_of_day": 8
}
```

### 6. Trip Planning Only
```http
POST /api/v1/trip
Content-Type: application/json
```

**Request Body:**
```json
{
  "origin_lat": -33.8688,
  "origin_lon": 151.2093,
  "destination_lat": -32.9283,
  "destination_lon": 151.7817
}
```

## Mobile App Integration

### iOS (Swift)

```swift
import Foundation

struct LocationIntelligence {
    let baseURL = "https://your-workspace.databricks.com/apps/nsw-ev-intelligence"
    
    func getIntelligence(lat: Double, lon: Double) async throws -> IntelligenceResponse {
        let url = URL(string: "\(baseURL)/api/v1/intelligence")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: Any] = [
            "lat": lat,
            "lon": lon,
            "max_distance_km": 20.0
        ]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(IntelligenceResponse.self, from: data)
    }
}
```

### Android (Kotlin)

```kotlin
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.POST

interface IntelligenceAPI {
    @POST("api/v1/intelligence")
    suspend fun getIntelligence(@Body request: IntelligenceRequest): IntelligenceResponse
}

class IntelligenceClient {
    private val retrofit = Retrofit.Builder()
        .baseUrl("https://your-workspace.databricks.com/apps/nsw-ev-intelligence/")
        .addConverterFactory(GsonConverterFactory.create())
        .build()
    
    private val api = retrofit.create(IntelligenceAPI::class.java)
    
    suspend fun getIntelligence(lat: Double, lon: Double): IntelligenceResponse {
        val request = IntelligenceRequest(
            lat = lat,
            lon = lon,
            max_distance_km = 20.0
        )
        return api.getIntelligence(request)
    }
}
```

### React Native (JavaScript)

```javascript
const API_BASE_URL = 'https://your-workspace.databricks.com/apps/nsw-ev-intelligence';

export async function getIntelligence(lat, lon) {
  const response = await fetch(`${API_BASE_URL}/api/v1/intelligence`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      lat,
      lon,
      max_distance_km: 20.0
    })
  });
  
  if (!response.ok) {
    throw new Error('API request failed');
  }
  
  return await response.json();
}
```

## Testing

### cURL Examples

**Test Health Endpoint:**
```bash
curl -X GET https://your-workspace.databricks.com/apps/nsw-ev-intelligence/health
```

**Test Intelligence Endpoint:**
```bash
curl -X POST https://your-workspace.databricks.com/apps/nsw-ev-intelligence/api/v1/intelligence \
  -H "Content-Type: application/json" \
  -d '{
    "lat": -33.8688,
    "lon": 151.2093,
    "max_distance_km": 20.0
  }'
```

**Test with Trip Planning:**
```bash
curl -X POST https://your-workspace.databricks.com/apps/nsw-ev-intelligence/api/v1/intelligence \
  -H "Content-Type: application/json" \
  -d '{
    "lat": -33.8688,
    "lon": 151.2093,
    "destination_lat": -32.9283,
    "destination_lon": 151.7817,
    "max_distance_km": 50.0
  }'
```

## Error Handling

### Error Response Format
```json
{
  "error": "Error message description"
}
```

### HTTP Status Codes
- `200 OK`: Request successful
- `400 Bad Request`: Missing or invalid parameters
- `500 Internal Server Error`: Server-side error

## Rate Limiting

Currently no rate limiting is enforced. For production deployment, consider adding:
- API key authentication
- Rate limiting per user/key
- Request throttling

## Security Considerations

1. **HTTPS Only**: Always use HTTPS in production
2. **CORS Configuration**: Configure allowed origins in `api_server.py`
3. **Input Validation**: All inputs are validated and sanitized
4. **SQL Injection**: Using parameterized queries with Spark SQL

## Performance

- **Average Response Time**: 2-5 seconds
- **Concurrent Requests**: Supports multiple concurrent users
- **Caching**: Consider adding Redis for frequently accessed locations

## Monitoring

Monitor these metrics:
- API response times
- Error rates
- Request volume
- Data freshness (gold table update times)

## Support

For issues or questions:
- **Email**: support@nsw-ev-intelligence.com
- **Documentation**: [Link to full documentation]
- **GitHub**: [Link to repository]

## License

Proprietary - NSW EV Intelligence Platform

## Version History

- **1.0.0** (2026-06-01): Initial release
  - Comprehensive intelligence endpoint
  - Charging stations endpoint
  - Fuel prices endpoint
  - Congestion forecast endpoint
  - Trip planning endpoint
  - Web UI
  - Mobile app integration support