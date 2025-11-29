import requests
from typing import Dict, Tuple, Optional, List
import math
import time
import os
from datetime import datetime

class FreeMapsService:
    """Free alternative to Google Maps using OpenStreetMap and OSRM"""
    
    def __init__(self):
        self.osrm_base = "https://router.project-osrm.org"
        self.nominatim_base = "https://nominatim.openstreetmap.org"
        self.user_agent = "MediSync/1.0 (Healthcare Queue Management)"
        self._geocode_cache = {}
        print("[OK] Free Maps Service initialized (OpenStreetMap + OSRM)")
    
    def geocode_address(self, address: str) -> Tuple[Optional[float], Optional[float]]:
        """Convert address to lat/lng using Nominatim (OpenStreetMap)"""
        # Check cache first
        if address in self._geocode_cache:
            return self._geocode_cache[address]
        
        try:
            params = {
                'q': address,
                'format': 'json',
                'limit': 1,
                'countrycodes': 'in'  # Restrict to India
            }
            headers = {'User-Agent': self.user_agent}
            
            response = requests.get(
                f"{self.nominatim_base}/search",
                params=params,
                headers=headers,
                timeout=10
            )
            
            # Nominatim requires respectful usage (1 request per second)
            time.sleep(1)
            
            if response.status_code == 200 and response.json():
                data = response.json()[0]
                coords = (float(data['lat']), float(data['lon']))
                self._geocode_cache[address] = coords
                print(f"[OK] Geocoded '{address}' -> {coords[0]:.4f}, {coords[1]:.4f}")
                return coords
        except Exception as e:
            print(f"[WARNING] Geocoding failed for '{address}': {e}")
        
        # Fallback to Mumbai coordinates
        fallback = self._get_mumbai_fallback(address)
        self._geocode_cache[address] = fallback
        return fallback
    
    def _get_mumbai_fallback(self, address: str) -> Tuple[float, float]:
        """Fallback geocoding for common Mumbai areas"""
        mumbai_areas = {
            "bandra west": (19.0596, 72.8295),
            "bandra": (19.0596, 72.8295),
            "andheri west": (19.1136, 72.8697),
            "andheri east": (19.1197, 72.8697),
            "andheri": (19.1136, 72.8697),
            "juhu": (19.1075, 72.8263),
            "powai": (19.1176, 72.9060),
            "goregaon": (19.1663, 72.8526),
            "malad": (19.1868, 72.8479),
            "borivali": (19.2304, 72.8581),
            "dadar": (19.0176, 72.8562),
            "kurla": (19.0728, 72.8826),
            "mumbai": (19.0760, 72.8777),
            "lilavati": (19.0596, 72.8295),
        }
        
        address_lower = address.lower()
        for area, coords in mumbai_areas.items():
            if area in address_lower:
                print(f"ℹ️ Using fallback coordinates for '{area}'")
                return coords
        
        print(f"ℹ️ Using default Mumbai coordinates")
        return (19.0760, 72.8777)
    
    def calculate_distance_time(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float]
    ) -> Dict:
        """Calculate distance and travel time using OSRM"""
        origin_lat, origin_lng = origin
        dest_lat, dest_lng = destination
        
        try:
            # OSRM expects lng,lat format
            url = f"{self.osrm_base}/route/v1/driving/{origin_lng},{origin_lat};{dest_lng},{dest_lat}"
            params = {'overview': 'false', 'steps': 'false', 'alternatives': 'false'}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 'Ok' and data.get('routes'):
                    route = data['routes'][0]
                    
                    distance_km = route['distance'] / 1000
                    duration_mins = route['duration'] / 60
                    
                    # Add traffic estimate (20-30% increase during peak hours)
                    hour = datetime.now().hour
                    is_peak = (9 <= hour <= 11) or (12 <= hour <= 14) or (16 <= hour <= 18)
                    traffic_multiplier = 1.3 if is_peak else 1.1
                    
                    traffic_duration_mins = duration_mins * traffic_multiplier
                    traffic_delay = traffic_duration_mins - duration_mins
                    
                    result = {
                        'distance_km': round(distance_km, 1),
                        'duration_minutes': round(duration_mins),
                        'traffic_duration_minutes': round(traffic_duration_mins),
                        'traffic_delay_minutes': round(traffic_delay),
                        'status': 'OK'
                    }
                    
                    print(f"[OK] Route: {result['distance_km']}km, {result['traffic_duration_minutes']}min")
                    return result
        except Exception as e:
            print(f"[WARNING] OSRM routing failed: {e}")
        
        # Fallback: Calculate straight-line distance
        return self._calculate_fallback_route(origin, destination)
    
    def _calculate_fallback_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float]
    ) -> Dict:
        """Calculate route using haversine distance with road factor"""
        distance_km = self._haversine_distance(origin, destination)
        
        # Apply road factor (roads are not straight lines)
        road_factor = 1.4
        actual_distance = distance_km * road_factor
        
        # Average speed in Mumbai: 20 km/h with traffic
        avg_speed = 20
        duration_mins = (actual_distance / avg_speed) * 60
        
        # Add traffic estimate
        hour = datetime.now().hour
        is_peak = (9 <= hour <= 11) or (12 <= hour <= 14) or (16 <= hour <= 18)
        traffic_multiplier = 1.4 if is_peak else 1.2
        
        traffic_duration_mins = duration_mins * traffic_multiplier
        
        print(f"ℹ️ Fallback: {actual_distance:.1f}km, {traffic_duration_mins:.0f}min")
        
        return {
            'distance_km': round(actual_distance, 1),
            'duration_minutes': round(duration_mins),
            'traffic_duration_minutes': round(traffic_duration_mins),
            'traffic_delay_minutes': round(traffic_duration_mins - duration_mins),
            'status': 'FALLBACK'
        }
    
    def _haversine_distance(
        self,
        coord1: Tuple[float, float],
        coord2: Tuple[float, float]
    ) -> float:
        """Calculate straight-line distance between two points"""
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        R = 6371  # Earth's radius in km
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        return distance
    
    def get_travel_time_with_traffic(
        self,
        patient_address: str,
        hospital_address: str
    ) -> Dict:
        """Main function to calculate travel time"""
        print(f"🗺️ Calculating route: '{patient_address}' -> '{hospital_address}'")
        
        # Geocode addresses
        patient_coords = self.geocode_address(patient_address)
        hospital_coords = self.geocode_address(hospital_address)
        
        if not patient_coords[0] or not hospital_coords[0]:
            return {
                'status': 'ERROR',
                'error': 'Could not geocode addresses',
                'distance_km': 10,
                'duration_minutes': 30,
                'traffic_duration_minutes': 40,
                'traffic_delay_minutes': 10
            }
        
        # Calculate route
        route_data = self.calculate_distance_time(patient_coords, hospital_coords)
        
        # Add address information
        route_data['origin_address'] = patient_address
        route_data['destination_address'] = hospital_address
        route_data['origin_coords'] = patient_coords
        route_data['destination_coords'] = hospital_coords
        
        return route_data
    
    def get_comprehensive_travel_data(
        self,
        origin_address: str,
        destination_address: str,
        travel_modes: List[str] = ["driving", "walking"]
    ) -> Dict:
        """Get comprehensive travel data (compatible with old Google Maps API)"""
        origin_coords = self.geocode_address(origin_address)
        dest_coords = self.geocode_address(destination_address)
        
        travel_options = {}
        
        # Driving mode
        if "driving" in travel_modes:
            route_data = self.calculate_distance_time(origin_coords, dest_coords)
            travel_options["driving"] = {
                "duration_mins": route_data.get("duration_minutes", 30),
                "traffic_duration_mins": route_data.get("traffic_duration_minutes", 35),
                "distance_km": route_data.get("distance_km", 10),
                "traffic_delay_mins": route_data.get("traffic_delay_minutes", 5),
                "status": route_data.get("status", "OK")
            }
        
        # Walking mode (roughly 5 km/h)
        if "walking" in travel_modes:
            distance = self._haversine_distance(origin_coords, dest_coords) * 1.3
            walking_time = (distance / 5) * 60
            travel_options["walking"] = {
                "duration_mins": round(walking_time),
                "distance_km": round(distance, 1),
                "status": "OK"
            }
        
        return {
            "status": "success",
            "origin": {
                "address": origin_address,
                "coordinates": list(origin_coords)
            },
            "destination": {
                "address": destination_address,
                "coordinates": list(dest_coords)
            },
            "travel_options": travel_options,
            "nearby_landmarks": [],
            "timestamp": datetime.utcnow().isoformat(),
            "source": "openstreetmap_osrm"
        }


# Global instance
_free_maps_instance = None

def get_free_maps_service() -> FreeMapsService:
    """Get singleton instance of FreeMapsService"""
    global _free_maps_instance
    if _free_maps_instance is None:
        _free_maps_instance = FreeMapsService()
    return _free_maps_instance


# --- Backward Compatibility Functions ---

def get_estimated_travel_time_with_traffic(
    origin: str,
    destination: str = "Lilavati Hospital, Bandra West, Mumbai, Maharashtra, India",
) -> Dict:
    """Backward compatible function for existing imports"""
    maps = get_free_maps_service()
    result = maps.get_travel_time_with_traffic(origin, destination)
    
    return {
        'status': result.get('status', 'OK'),
        'normal_duration_mins': result.get('duration_minutes', 30),
        'traffic_duration_mins': result.get('traffic_duration_minutes', 35),
        'distance_km': result.get('distance_km', 10),
        'traffic_delay_mins': result.get('traffic_delay_minutes', 5),
        'origin': origin,
        'destination': destination
    }


def check_traffic_conditions(
    origin: str,
    destination: str = "Lilavati Hospital, Bandra West, Mumbai, Maharashtra, India",
) -> str:
    """Check current traffic conditions for the route"""
    travel_data = get_estimated_travel_time_with_traffic(origin, destination)
    
    delay = travel_data['traffic_delay_mins']
    
    if delay <= 2:
        return f"🟢 Light traffic - Normal conditions ({travel_data['traffic_duration_mins']} min)"
    elif delay <= 10:
        return f"🟡 Moderate traffic - {delay} min delay ({travel_data['traffic_duration_mins']} min total)"
    else:
        return f"🔴 Heavy traffic - {delay} min delay ({travel_data['traffic_duration_mins']} min total)"


def get_real_clinic_location() -> str:
    """Get the actual clinic location from environment"""
    return os.getenv(
        "CLINIC_ADDRESS", "Lilavati Hospital, Bandra West, Mumbai, Maharashtra, India"
    )


def get_comprehensive_patient_travel_data(patient_location: str) -> Dict:
    """Get comprehensive travel data for patient location to clinic"""
    maps = get_free_maps_service()
    clinic_location = get_real_clinic_location()
    return maps.get_comprehensive_travel_data(patient_location, clinic_location)


def geocode_patient_location(location_description: str) -> Dict:
    """Convert patient location to precise coordinates"""
    maps = get_free_maps_service()
    coords = maps.geocode_address(location_description)
    
    return {
        "status": "success" if coords[0] else "failed",
        "lat": coords[0],
        "lng": coords[1],
        "formatted_address": location_description,
        "source": "openstreetmap"
    }