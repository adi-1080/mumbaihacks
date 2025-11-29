import os
import googlemaps
import requests
from datetime import datetime
from typing import Dict, Tuple, Optional, List
import json


class AdvancedMapsIntegration:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            print("[ERROR] Google Maps API key not found in environment variables")
            self.gmaps = None
        else:
            self.gmaps = googlemaps.Client(key=self.api_key)
            print("[OK] Advanced Google Maps client initialized successfully")

    def get_current_location_from_ip(self) -> Dict:
        """
        Get approximate location from IP address as fallback.

        Returns:
            Dictionary with location data
        """
        try:
            # Using a free IP geolocation service
            response = requests.get("http://ip-api.com/json/")
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "lat": data.get("lat"),
                    "lng": data.get("lon"),
                    "address": f"{data.get('city', '')}, {data.get('regionName', '')}, {data.get('country', '')}",
                    "source": "ip_geolocation",
                }
        except Exception as e:
            print(f"[ERROR] IP Geolocation failed: {e}")

        return {"status": "failed", "source": "ip_geolocation"}

    def geocode_address(self, address: str) -> Dict:
        """
        Convert address to precise latitude/longitude coordinates.

        Args:
            address: Street address or location description

        Returns:
            Dictionary with geocoded location data
        """
        if not self.gmaps:
            return self._fallback_geocoding(address)

        try:
            print(f"[TOOL] [Maps API] Geocoding address: '{address}'")

            # Use Google Geocoding API
            geocode_result = self.gmaps.geocode(address)

            if geocode_result:
                location = geocode_result[0]["geometry"]["location"]
                formatted_address = geocode_result[0]["formatted_address"]

                # Get place details if available
                place_types = geocode_result[0].get("types", [])

                result = {
                    "status": "success",
                    "lat": location["lat"],
                    "lng": location["lng"],
                    "formatted_address": formatted_address,
                    "place_types": place_types,
                    "source": "google_geocoding",
                }

                print(
                    f"[OK] [Maps API] Geocoded to: {location['lat']}, {location['lng']}"
                )
                return result

        except Exception as e:
            print(f"[ERROR] [Maps API] Geocoding error: {e}")

        return self._fallback_geocoding(address)

    def get_comprehensive_travel_data(
        self,
        origin_address: str,
        destination_address: str,
        travel_modes: List[str] = ["driving", "walking", "transit"],
    ) -> Dict:
        """
        Get comprehensive travel data for multiple modes of transport.

        Args:
            origin_address: Starting location
            destination_address: Destination location
            travel_modes: List of travel modes to check

        Returns:
            Comprehensive travel data dictionary
        """
        if not self.gmaps:
            return self._fallback_comprehensive_travel(
                origin_address, destination_address
            )

        try:
            print(
                f"[TOOL] [Maps API] Getting comprehensive travel data from '{origin_address}' to '{destination_address}'"
            )

            # Geocode both addresses first for precision
            origin_geo = self.geocode_address(origin_address)
            dest_geo = self.geocode_address(destination_address)

            if origin_geo["status"] != "success" or dest_geo["status"] != "success":
                return self._fallback_comprehensive_travel(
                    origin_address, destination_address
                )

            travel_options = {}

            for mode in travel_modes:
                try:
                    # Get distance matrix for each mode
                    matrix_result = self.gmaps.distance_matrix(
                        origins=[f"{origin_geo['lat']},{origin_geo['lng']}"],
                        destinations=[f"{dest_geo['lat']},{dest_geo['lng']}"],
                        mode=mode,
                        departure_time=datetime.now(),
                        traffic_model="best_guess" if mode == "driving" else None,
                        units="metric",
                    )

                    if (
                        matrix_result["status"] == "OK"
                        and matrix_result["rows"][0]["elements"][0]["status"] == "OK"
                    ):

                        element = matrix_result["rows"][0]["elements"][0]

                        # For driving, get both normal and traffic duration
                        if mode == "driving":
                            duration_in_traffic = element.get(
                                "duration_in_traffic", element["duration"]
                            )
                            travel_options[mode] = {
                                "duration_mins": round(
                                    element["duration"]["value"] / 60
                                ),
                                "traffic_duration_mins": round(
                                    duration_in_traffic["value"] / 60
                                ),
                                "distance_km": round(
                                    element["distance"]["value"] / 1000, 1
                                ),
                                "traffic_delay_mins": round(
                                    (
                                        duration_in_traffic["value"]
                                        - element["duration"]["value"]
                                    )
                                    / 60
                                ),
                                "status": "success",
                            }
                        else:
                            travel_options[mode] = {
                                "duration_mins": round(
                                    element["duration"]["value"] / 60
                                ),
                                "distance_km": round(
                                    element["distance"]["value"] / 1000, 1
                                ),
                                "status": "success",
                            }

                        print(
                            f"[OK] [Maps API] {mode.title()}: {travel_options[mode]['duration_mins']}min"
                        )

                except Exception as mode_error:
                    print(f"[ERROR] [Maps API] Error for {mode}: {mode_error}")
                    travel_options[mode] = {
                        "status": "failed",
                        "error": str(mode_error),
                    }

            # Get nearby places for context
            nearby_places = self._get_nearby_landmarks(
                origin_geo["lat"], origin_geo["lng"]
            )

            return {
                "status": "success",
                "origin": {
                    "address": origin_geo["formatted_address"],
                    "coordinates": [origin_geo["lat"], origin_geo["lng"]],
                },
                "destination": {
                    "address": dest_geo["formatted_address"],
                    "coordinates": [dest_geo["lat"], dest_geo["lng"]],
                },
                "travel_options": travel_options,
                "nearby_landmarks": nearby_places,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "google_maps_comprehensive",
            }

        except Exception as e:
            print(f"[ERROR] [Maps API] Comprehensive travel error: {e}")
            return self._fallback_comprehensive_travel(
                origin_address, destination_address
            )

    def _get_nearby_landmarks(
        self, lat: float, lng: float, radius: int = 500
    ) -> List[Dict]:
        """Get nearby landmarks for location context"""
        if not self.gmaps:
            return []

        try:
            places_result = self.gmaps.places_nearby(
                location=(lat, lng), radius=radius, type="point_of_interest"
            )

            landmarks = []
            for place in places_result.get("results", [])[:3]:  # Top 3 landmarks
                landmarks.append(
                    {
                        "name": place.get("name"),
                        "types": place.get("types", []),
                        "rating": place.get("rating"),
                        "vicinity": place.get("vicinity"),
                    }
                )

            return landmarks

        except Exception as e:
            print(f"[ERROR] [Maps API] Nearby places error: {e}")
            return []

    def _fallback_geocoding(self, address: str) -> Dict:
        """Fallback geocoding using approximate coordinates"""
        # Mumbai coordinates for common areas
        mumbai_areas = {
            "bandra west": {"lat": 19.0596, "lng": 72.8295},
            "bandra": {"lat": 19.0596, "lng": 72.8295},
            "mumbai": {"lat": 19.0760, "lng": 72.8777},
            "andheri": {"lat": 19.1136, "lng": 72.8697},
            "juhu": {"lat": 19.1075, "lng": 72.8263},
            "powai": {"lat": 19.1176, "lng": 72.9060},
        }

        address_lower = address.lower()
        for area, coords in mumbai_areas.items():
            if area in address_lower:
                return {
                    "status": "fallback",
                    "lat": coords["lat"],
                    "lng": coords["lng"],
                    "formatted_address": address,
                    "source": "fallback_geocoding",
                }

        return {
            "status": "failed",
            "source": "fallback_geocoding",
            "lat": 19.0760,
            "lng": 72.8777,
            "formatted_address": address,
        }

    def _fallback_comprehensive_travel(self, origin: str, destination: str) -> Dict:
        """Fallback when Maps API is unavailable"""
        import random

        return {
            "status": "fallback",
            "origin": {"address": origin, "coordinates": [19.0596, 72.8295]},
            "destination": {"address": destination, "coordinates": [19.0760, 72.8777]},
            "travel_options": {
                "driving": {
                    "duration_mins": random.randint(20, 45),
                    "traffic_duration_mins": random.randint(25, 60),
                    "distance_km": random.randint(5, 15),
                    "traffic_delay_mins": random.randint(5, 15),
                    "status": "fallback",
                },
                "walking": {
                    "duration_mins": random.randint(60, 120),
                    "distance_km": random.randint(3, 10),
                    "status": "fallback",
                },
            },
            "source": "fallback_system",
            "nearby_landmarks": [],
        }


# Global instance
advanced_maps = AdvancedMapsIntegration()

# --- Backward Compatibility Functions ---
# These are the functions other modules are trying to import


def get_estimated_travel_time_with_traffic(
    origin: str,
    destination: str = "Lilavati Hospital, Bandra West, Mumbai, Maharashtra, India",
) -> Dict:
    """
    Backward compatible function for existing imports.

    Args:
        origin: Starting location
        destination: Destination location

    Returns:
        Travel data dictionary
    """
    travel_data = advanced_maps.get_comprehensive_travel_data(origin, destination)

    # Extract driving data for backward compatibility
    driving_data = travel_data.get("travel_options", {}).get("driving", {})

    return {
        "status": travel_data.get("status", "fallback"),
        "normal_duration_mins": driving_data.get("duration_mins", 30),
        "traffic_duration_mins": driving_data.get("traffic_duration_mins", 35),
        "distance_km": driving_data.get("distance_km", 10),
        "traffic_delay_mins": driving_data.get("traffic_delay_mins", 5),
        "origin": origin,
        "destination": destination,
    }


def check_traffic_conditions(
    origin: str,
    destination: str = "Lilavati Hospital, Bandra West, Mumbai, Maharashtra, India",
) -> str:
    """
    Check current traffic conditions for the route.

    Returns:
        String description of traffic conditions
    """
    travel_data = get_estimated_travel_time_with_traffic(origin, destination)

    if travel_data["status"] == "fallback":
        return "Traffic data unavailable - using estimated times"

    delay = travel_data["traffic_delay_mins"]

    if delay <= 2:
        return f"🟢 Light traffic - Normal conditions ({travel_data['traffic_duration_mins']} min)"
    elif delay <= 10:
        return f"🟡 Moderate traffic - {delay} min delay ({travel_data['traffic_duration_mins']} min total)"
    else:
        return f"🔴 Heavy traffic - {delay} min delay ({travel_data['traffic_duration_mins']} min total)"


# --- New Enhanced Functions ---


def get_real_clinic_location() -> str:
    """
    Get the actual clinic location.
    In production, this would come from database/config.
    """
    return os.getenv(
        "CLINIC_ADDRESS", "Lilavati Hospital, Bandra West, Mumbai, Maharashtra, India"
    )


def get_comprehensive_patient_travel_data(patient_location: str) -> Dict:
    """
    Get comprehensive travel data for patient location to clinic.

    Args:
        patient_location: Patient's location description

    Returns:
        Complete travel analysis
    """
    clinic_location = get_real_clinic_location()
    return advanced_maps.get_comprehensive_travel_data(
        patient_location, clinic_location
    )


def geocode_patient_location(location_description: str) -> Dict:
    """
    Convert patient location to precise coordinates.

    Args:
        location_description: Patient's location description

    Returns:
        Geocoded location data
    """
    return advanced_maps.geocode_address(location_description)
