"""Intelligence service for EV charging station queries and analysis"""
from typing import Dict, Optional
from datetime import datetime
from src.services.sql_service import get_sql_connection
from src.config.settings import CHARGER_TABLE, DEFAULT_MAX_DISTANCE_KM, DEFAULT_LIMIT_STATIONS

def get_consumer_intelligence(
    lat: float,
    lon: float,
    postcode: Optional[str] = None,
    charger_type: Optional[str] = None,
    fuel_type: Optional[str] = None,
    destination_lat: Optional[float] = None,
    destination_lon: Optional[float] = None,
    max_distance_km: float = DEFAULT_MAX_DISTANCE_KM,
    hour_of_day: Optional[int] = None
) -> Dict:
    """
    Get consumer intelligence for EV charging stations and route planning
    
    Args:
        lat, lon: User location coordinates
        postcode: Optional postcode filter
        charger_type: Optional charger type filter (AC, DC, etc.)
        fuel_type: Optional fuel type (for future features)
        destination_lat, destination_lon: Optional destination coordinates
        max_distance_km: Maximum search radius in kilometers
        hour_of_day: Optional hour for congestion forecasts
        
    Returns:
        Dictionary containing status, insights, and recommendations
    """
    conn = get_sql_connection()
    
    if conn is None:
        return {
            "status": "limited",
            "message": "Running in limited mode - Database connection not available",
            "insights": {
                "charging_stations": {
                    "stations_found": 0,
                    "message": "Database required for queries"
                },
                "fuel_options": {
                    "regions_found": 0,
                    "message": "Database required for queries"
                },
                "congestion_forecast": {
                    "nearby_risk_areas": [],
                    "message": "Database required for queries"
                },
                "trip_intelligence": None
            }
        }
    
    try:
        insights = {}
        
        # ========================================================================
        # Query nearest charging stations
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
                FROM {CHARGER_TABLE}
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
            
            sql_query += f" ORDER BY distance_km ASC LIMIT {DEFAULT_LIMIT_STATIONS}"
            
            print(f"Executing SQL query for lat={lat}, lon={lon}")
            cursor.execute(sql_query)
            
            # Fetch and format results
            charging_stations = []
            for row in cursor.fetchall():
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
        # Fuel options (placeholder for future features)
        # ========================================================================
        insights["fuel_options"] = {
            "regions_found": 0,
            "fuel_recommendations": [],
            "message": "Feature coming soon"
        }
        
        # ========================================================================
        # Congestion forecast (placeholder for future features)
        # ========================================================================
        insights["congestion_forecast"] = {
            "nearby_risk_areas": [],
            "message": "Feature coming soon"
        }
        
        # ========================================================================
        # Trip intelligence (placeholder for future features)
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
