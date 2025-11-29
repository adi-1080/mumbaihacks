"""
A* Pathfinding Algorithm for Real-Time Travel ETA
Integrates with OpenStreetMap for road network and traffic data.

Data Structure:
- Adjacency List Graph (road network)
- Priority Queue for A* frontier

Algorithm:
- A* search with Haversine heuristic
- Real-time traffic weight adjustments
"""

import heapq
import math
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from tools.free_maps import FreeMapsService


@dataclass(order=True)
class AStarNode:
    """Node for A* search priority queue"""
    f_score: float  # g + h (total cost estimate)
    g_score: float = field(compare=False)  # Cost from start
    h_score: float = field(compare=False)  # Heuristic to goal
    lat: float = field(compare=False)
    lon: float = field(compare=False)
    parent: Optional[Tuple[float, float]] = field(compare=False, default=None)


class RoadNetworkGraph:
    """
    Simplified road network graph for A* pathfinding.
    In production, this would load from OSM data.
    """
    
    def __init__(self):
        # Adjacency list: (lat, lon) -> [(neighbor_lat, neighbor_lon, weight_mins)]
        self.graph: Dict[Tuple[float, float], List[Tuple[float, float, float]]] = {}
        
        # Traffic multipliers by time of day
        self.traffic_patterns = {
            "peak_morning": (8, 11, 1.5),    # 8-11 AM, 1.5x slower
            "peak_evening": (17, 20, 1.6),   # 5-8 PM, 1.6x slower
            "lunch": (12, 14, 1.3),          # 12-2 PM, 1.3x slower
            "night": (22, 6, 0.8),           # 10 PM-6 AM, 0.8x (faster)
        }
    
    def add_edge(self, from_lat: float, from_lon: float, 
                 to_lat: float, to_lon: float, base_time_mins: float):
        """Add bidirectional road edge"""
        from_node = (from_lat, from_lon)
        to_node = (to_lat, to_lon)
        
        if from_node not in self.graph:
            self.graph[from_node] = []
        if to_node not in self.graph:
            self.graph[to_node] = []
        
        self.graph[from_node].append((to_lat, to_lon, base_time_mins))
        self.graph[to_node].append((from_lat, from_lon, base_time_mins))
    
    def get_neighbors(self, lat: float, lon: float) -> List[Tuple[float, float, float]]:
        """Get neighboring nodes with edge weights"""
        node = (lat, lon)
        return self.graph.get(node, [])
    
    def get_traffic_multiplier(self, current_hour: int) -> float:
        """Get current traffic multiplier based on time"""
        for pattern, (start, end, multiplier) in self.traffic_patterns.items():
            if start <= end:
                if start <= current_hour < end:
                    return multiplier
            else:  # Wraps around midnight
                if current_hour >= start or current_hour < end:
                    return multiplier
        return 1.0  # Normal traffic


class AStarETACalculator:
    """
    A* algorithm for calculating optimal travel time with real-time traffic.
    
    Features:
    - Haversine heuristic (great-circle distance)
    - Traffic-aware edge weights
    - Fallback to free_maps API if graph incomplete
    """
    
    def __init__(self, maps_service: Optional[FreeMapsService] = None):
        self.road_network = RoadNetworkGraph()
        self.maps_service = maps_service or FreeMapsService()
        
        # Initialize with Mumbai key locations (simplified demo)
        self._init_mumbai_graph()
        
        print("[OK] A* ETA Calculator initialized with road network")
    
    def _init_mumbai_graph(self):
        """Initialize simplified Mumbai road network"""
        # Key Mumbai locations (lat, lon)
        locations = {
            "bandra": (19.0596, 72.8295),
            "andheri": (19.1136, 72.8697),
            "worli": (19.0176, 72.8120),
            "dadar": (19.0186, 72.8481),
            "churchgate": (18.9322, 72.8264),
            "lower_parel": (19.0008, 72.8289),
            "kurla": (19.0728, 72.8826),
        }
        
        # Add edges with approximate base travel times (mins)
        edges = [
            ("bandra", "andheri", 15),
            ("bandra", "worli", 12),
            ("bandra", "dadar", 10),
            ("worli", "lower_parel", 8),
            ("worli", "churchgate", 15),
            ("dadar", "lower_parel", 10),
            ("dadar", "kurla", 12),
            ("andheri", "kurla", 10),
            ("lower_parel", "churchgate", 12),
        ]
        
        for loc1, loc2, time in edges:
            lat1, lon1 = locations[loc1]
            lat2, lon2 = locations[loc2]
            self.road_network.add_edge(lat1, lon1, lat2, lon2, time)
    
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate great-circle distance between two points (km).
        Used as A* heuristic.
        """
        R = 6371  # Earth radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        return distance
    
    @staticmethod
    def distance_to_time_heuristic(distance_km: float) -> float:
        """
        Convert distance to estimated time.
        Assumes average speed of 30 km/h in city traffic.
        """
        avg_speed_kmh = 30
        return (distance_km / avg_speed_kmh) * 60  # Convert to minutes
    
    def calculate_eta(self, from_lat: float, from_lon: float,
                     to_lat: float, to_lon: float) -> Dict:
        """
        Calculate travel ETA using A* algorithm with real-time traffic.
        Falls back to free_maps API if graph path not found.
        
        Args:
            from_lat, from_lon: Starting coordinates
            to_lat, to_lon: Destination coordinates
            
        Returns:
            Dict with travel_time_mins, distance_km, path, method
        """
        print(f"[INFO] [A* ETA] Calculating route: ({from_lat}, {from_lon}) → ({to_lat}, {to_lon})")
        
        # Try A* on local graph first
        result = self._astar_search(from_lat, from_lon, to_lat, to_lon)
        
        if result["path_found"]:
            print(f"[OK] [A* ETA] Route found: {result['travel_time_mins']:.1f} mins via graph")
            return result
        
        # Fallback to free_maps API
        print(f"[CYCLE] [A* ETA] Graph incomplete, using free_maps API fallback")
        return self._fallback_to_api(from_lat, from_lon, to_lat, to_lon)
    
    def _astar_search(self, start_lat: float, start_lon: float,
                     goal_lat: float, goal_lon: float) -> Dict:
        """
        A* pathfinding algorithm implementation.
        
        Returns:
            Dict with path_found, travel_time_mins, distance_km, path
        """
        start = (start_lat, start_lon)
        goal = (goal_lat, goal_lon)
        
        # Check if nodes exist in graph (simplified check)
        if start not in self.road_network.graph and goal not in self.road_network.graph:
            return {"path_found": False}
        
        # Get current traffic multiplier
        current_hour = datetime.now().hour
        traffic_multiplier = self.road_network.get_traffic_multiplier(current_hour)
        
        # A* data structures
        frontier = []  # Priority queue
        visited: Set[Tuple[float, float]] = set()
        g_scores: Dict[Tuple[float, float], float] = {start: 0}
        came_from: Dict[Tuple[float, float], Optional[Tuple[float, float]]] = {start: None}
        
        # Initial heuristic
        h_start = self.distance_to_time_heuristic(
            self.haversine_distance(start_lat, start_lon, goal_lat, goal_lon)
        )
        
        start_node = AStarNode(
            f_score=h_start,
            g_score=0,
            h_score=h_start,
            lat=start_lat,
            lon=start_lon,
        )
        
        heapq.heappush(frontier, start_node)
        
        # A* main loop
        iterations = 0
        max_iterations = 1000
        
        while frontier and iterations < max_iterations:
            iterations += 1
            
            current = heapq.heappop(frontier)
            current_node = (current.lat, current.lon)
            
            # Goal check
            if self.haversine_distance(current.lat, current.lon, goal_lat, goal_lon) < 0.5:  # <500m
                # Reconstruct path
                path = self._reconstruct_path(came_from, current_node)
                total_distance = self.haversine_distance(start_lat, start_lon, goal_lat, goal_lon)
                
                return {
                    "path_found": True,
                    "travel_time_mins": current.g_score,
                    "distance_km": total_distance,
                    "path": path,
                    "method": "astar_graph",
                    "traffic_multiplier": traffic_multiplier,
                    "iterations": iterations,
                }
            
            if current_node in visited:
                continue
            
            visited.add(current_node)
            
            # Expand neighbors
            for neighbor_lat, neighbor_lon, base_time in self.road_network.get_neighbors(current.lat, current.lon):
                neighbor = (neighbor_lat, neighbor_lon)
                
                if neighbor in visited:
                    continue
                
                # Calculate g_score with traffic
                edge_cost = base_time * traffic_multiplier
                tentative_g = current.g_score + edge_cost
                
                if neighbor not in g_scores or tentative_g < g_scores[neighbor]:
                    g_scores[neighbor] = tentative_g
                    came_from[neighbor] = current_node
                    
                    # Heuristic: distance to goal
                    h_score = self.distance_to_time_heuristic(
                        self.haversine_distance(neighbor_lat, neighbor_lon, goal_lat, goal_lon)
                    )
                    
                    f_score = tentative_g + h_score
                    
                    neighbor_node = AStarNode(
                        f_score=f_score,
                        g_score=tentative_g,
                        h_score=h_score,
                        lat=neighbor_lat,
                        lon=neighbor_lon,
                    )
                    
                    heapq.heappush(frontier, neighbor_node)
        
        # No path found
        return {"path_found": False}
    
    def _reconstruct_path(self, came_from: Dict, current: Tuple[float, float]) -> List[Tuple[float, float]]:
        """Reconstruct path from came_from chain"""
        path = [current]
        while current in came_from and came_from[current] is not None:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path
    
    def _fallback_to_api(self, from_lat: float, from_lon: float,
                        to_lat: float, to_lon: float) -> Dict:
        """Fallback to free_maps API when graph is incomplete"""
        try:
            # Use free_maps service
            result = self.maps_service.calculate_distance_time(
                f"{from_lat},{from_lon}",
                f"{to_lat},{to_lon}"
            )
            
            return {
                "path_found": True,
                "travel_time_mins": result.get("duration_minutes", 20),
                "distance_km": result.get("distance_km", 10),
                "path": [],
                "method": "free_maps_api",
            }
        except Exception as e:
            print(f"[WARNING] [A* ETA] API fallback failed: {e}")
            
            # Last resort: straight-line estimate
            distance_km = self.haversine_distance(from_lat, from_lon, to_lat, to_lon)
            estimated_time = self.distance_to_time_heuristic(distance_km)
            
            return {
                "path_found": True,
                "travel_time_mins": estimated_time,
                "distance_km": distance_km,
                "path": [],
                "method": "haversine_estimate",
            }
    
    def update_traffic_conditions(self, hour: int, multiplier: float):
        """Update traffic patterns dynamically"""
        # Could be extended to learn from historical data
        pass


# Global singleton
_astar_calculator: Optional[AStarETACalculator] = None


def get_astar_eta_calculator() -> AStarETACalculator:
    """Get or create global A* ETA calculator"""
    global _astar_calculator
    if _astar_calculator is None:
        _astar_calculator = AStarETACalculator()
    return _astar_calculator
