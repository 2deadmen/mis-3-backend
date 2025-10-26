import firebase_admin
from firebase_admin import firestore, credentials
from geopy.distance import geodesic
from typing import List, Dict, Tuple


class GeminiCityDataGetter:
    def __init__(self):
        if not firebase_admin._apps:
            cred = credentials.Certificate("./firebasekey.json")
            firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    def get_relevant_incidents(
        self,
        user_preferences: Dict = None,
        user_location: Tuple[float, float] = None,
        radius_km: float = 10
    ) -> List[Dict]:
        """
        Fetches all incidents from Firestore within a given radius of the user location.
        Prioritizes key event categories.
        If user_location is None, returns all incidents.
        """
        PRIORITY_CATEGORIES = [
            "Flood", "Power Cut", "Road Block", "Accident", "Fire", "Flash Mob", "Garbage", "Tree Fall", "Stampede"
        ]
        events = self.db.collection("bangalore").document("incidents").collection("all").stream()

        priority_incidents = []
        other_incidents = []
        for doc in events:
            data = doc.to_dict()
            location = data.get("location")
            if not location:
                continue
            if user_location:
                # Support both dict and GeoPoint
                if isinstance(location, dict):
                    inc_lat = location.get("lat")
                    inc_lng = location.get("lng")
                else:
                    inc_lat = getattr(location, "latitude", None)
                    inc_lng = getattr(location, "longitude", None)
                if inc_lat is None or inc_lng is None:
                    continue
                distance_km = geodesic(user_location, (inc_lat, inc_lng)).km
                if distance_km > radius_km:
                    continue
                data["distance"] = distance_km
            category = data.get("category")
            incident = {"id": doc.id, **data}
            if category in PRIORITY_CATEGORIES:
                priority_incidents.append(incident)
            else:
                other_incidents.append(incident)

        # Sort by distance if available, otherwise keep order
        priority_incidents.sort(key=lambda x: x.get("distance", 0))
        other_incidents.sort(key=lambda x: x.get("distance", 0))
        return priority_incidents + other_incidents

    def get_incidents_along_route(
        self,
        src_lat: float,
        src_lng: float,
        dest_lat: float,
        dest_lng: float,
        step_km: float = 2,
        corridor_radius_km: float = 1.5
    ) -> List[Dict]:
        """
        Fetch incidents that occur along the route between source and destination.

        Args:
            src_lat (float): Source latitude.
            src_lng (float): Source longitude.
            dest_lat (float): Destination latitude.
            dest_lng (float): Destination longitude.
            step_km (float): Distance between interpolation waypoints.
            corridor_radius_km (float): Radius around waypoints to consider.

        Returns:
            List[dict]: Incidents near the defined route corridor.
        """
        # creates straight line from A-B 
        def interpolate_points(
            lat1: float, lng1: float, lat2: float, lng2: float, steps: int
        ) -> List[Tuple[float, float]]:
            return [
                (
                    lat1 + (lat2 - lat1) * i / steps,
                    lng1 + (lng2 - lng1) * i / steps
                )
                for i in range(steps + 1)
            ]

        total_distance = geodesic((src_lat, src_lng), (dest_lat, dest_lng)).km
        steps = max(1, int(total_distance // step_km))
        waypoints = interpolate_points(src_lat, src_lng, dest_lat, dest_lng, steps)

        seen_ids = set()
        matched_incidents = []

        # Search in the correct collection: 'all' instead of 'events'
        all_incidents = self.db.collection("bangalore").document("incidents").collection("all").stream()

        for doc in all_incidents:
            data = doc.to_dict()
            incident_location = data.get("location")
            if not incident_location or doc.id in seen_ids:
                continue

            for lat, lng in waypoints:
                # Support both dict and GeoPoint for location
                if isinstance(incident_location, dict):
                    inc_lat = incident_location.get("lat")
                    inc_lng = incident_location.get("lng")
                else:
                    inc_lat = getattr(incident_location, "latitude", None)
                    inc_lng = getattr(incident_location, "longitude", None)
                if inc_lat is None or inc_lng is None:
                    continue
                dist = geodesic((lat, lng), (inc_lat, inc_lng)).km
                if dist <= corridor_radius_km:
                    matched_incidents.append({**data, "distance_from_route": dist})
                    seen_ids.add(doc.id)
                    break  # No need to check other waypoints for this incident

        return matched_incidents
