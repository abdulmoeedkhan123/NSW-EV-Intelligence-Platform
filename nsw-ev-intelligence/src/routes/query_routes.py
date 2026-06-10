"""API routes for charging station queries"""
from flask import Blueprint, request, jsonify
from src.services.intelligence_service import get_consumer_intelligence

query_bp = Blueprint('query', __name__)

@query_bp.route('/query', methods=['POST'])
def query_intelligence():
    """
    Main query endpoint for consumer intelligence
    
    Request body (JSON):
        - latitude (float, required): User's latitude
        - longitude (float, required): User's longitude
        - postcode (str, optional): Postcode filter
        - charger_type (str, optional): Charger type filter (AC, DC, etc.)
        - fuel_type (str, optional): Fuel type filter
        - max_distance_km (float, optional): Search radius in km (default: 30)
        - destination_lat (float, optional): Destination latitude
        - destination_lon (float, optional): Destination longitude
        - hour_of_day (int, optional): Hour for congestion forecasts
        
    Returns:
        JSON response with charging stations and intelligence insights
    """
    try:
        data = request.get_json()
        
        # Extract and validate required parameters
        lat = float(data.get('latitude'))
        lon = float(data.get('longitude'))
        
        # Extract optional parameters
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
        
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": f"Invalid parameter format: {str(e)}"
        }), 400
    except KeyError as e:
        return jsonify({
            "status": "error",
            "message": f"Missing required parameter: {str(e)}"
        }), 400
    except Exception as e:
        print(f"Error in /query endpoint: {e}")
        return jsonify({
            "status": "error",
            "message": f"Request processing error: {str(e)}"
        }), 500
