"""Utility helper functions"""
from math import radians, cos, sin, asin, sqrt
from typing import Optional

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> Optional[float]:
    """Calculate distance between two points in kilometers"""
    if None in [lat1, lon1, lat2, lon2]:
        return None
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    return c * 6371