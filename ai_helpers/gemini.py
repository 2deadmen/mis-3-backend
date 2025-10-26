import firebase_admin
import os 
from firebase_admin import credentials, firestore
from google import genai
from google.genai import types
from datetime import datetime, timedelta
from google.cloud.firestore_v1 import GeoPoint
import json
import requests
import math

class GeminiCityAnalyzer:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))
        key_path = os.path.join(os.path.dirname(__file__), '..', 'firebasekey.json')
        
        if not firebase_admin._apps:
            cred = credentials.Certificate(os.path.abspath(key_path))
            firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371  # Earth radius in km
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        d_phi = math.radians(lat2 - lat1)
        d_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(d_phi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c  # Distance in km

    def analyze_incident(self, image_url: str, lat: float, lng: float, area: str) -> dict:
        # 🔽 Step 1: Download image
        try:
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            image_bytes = image_response.content
        except Exception as e:
            return {"error": f"Failed to fetch image: {str(e)}"}

        # 🔽 Step 2: Prepare image part
        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")

        # 🔽 Step 3: Prompt
        prompt = f"""
You are a city AI safety assistant analyzing civic incidents from citizen-submitted photos in Bengaluru. Your job is to classify events such as floods, accidents, stampedes, power outages, fire incidents, garbage accumulation, potholes, etc., and return a structured report.
Analyze the attached photo. Based on visible context, determine:
- The type of incident (use categories below)
- A short summary of the situation
- Severity (Low, Medium, High)
- The approximate human-readable area name (e.g., "Jayanagar", "HSR Layout")
- The approximate postal code (zipcode)

Use ONLY one of the following categories:
["Flood", "Pothole", "Power Cut", "Road Block", "Accident", "Fire", "Flash Mob", "Garbage", "Tree Fall", "Stampede", "Other"]

Return ONLY this exact JSON format:
{{
  "category": "...",
  "summary": "...",
  "severity": "...",
  "location": {{ "lat": {lat}, "lng": {lng} }},
  "timestamp": "{datetime.utcnow().isoformat()}Z",
  "image_url": "{image_url}",
  "area": "{area}",
  "zipcode": "..."
}}
Only return clean JSON. Do not include markdown or extra explanation.
"""

        # 🔽 Step 4: Gemini call
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[image_part, prompt]
            )
            result = json.loads(response.text)
        except Exception as e:
            return {"error": f"Gemini API failed: {str(e)}"}

        try:
            incident_data = result
            incident_data["geo"] = GeoPoint(lat, lng)

            category = incident_data.get("category")
            timestamp = datetime.utcnow()
            incident_data["timestamp"] = timestamp

            # 🔽 Step 5: Deduplication check
            fifteen_minutes_ago = timestamp - timedelta(minutes=15)
            incidents_ref = self.db.collection("bangalore").document("incidents").collection("all")
            recent_snapshots = incidents_ref.where("category", "==", category).stream()

            for doc in recent_snapshots:
                data = doc.to_dict()
                loc = data.get("location")
                ts = data.get("timestamp")

                if not loc or not ts:
                    continue

                # Convert Firestore timestamp or string to offset-naive UTC datetime
                if hasattr(ts, 'astimezone'):
                    ts = ts.astimezone(tz=None).replace(tzinfo=None)
                elif isinstance(ts, str):
                    try:
                        ts = datetime.fromisoformat(ts.replace("Z", ""))
                    except Exception:
                        continue

                if ts < fifteen_minutes_ago:
                    continue

                distance_km = self.haversine(lat, lng, loc["lat"], loc["lng"])
                if distance_km <= 0.1:  # Within 100 meters
                    # Save in duplicates collection
                    self.db.collection("bangalore").document("incidents").collection("duplicates").add(incident_data)
                    return {"message": "Duplicate incident detected. Logged to duplicates.", "duplicate": True}

            # 🔽 Step 6: Save new unique incident
            doc_ref = incidents_ref.document()
            doc_ref.set(incident_data)
            return {"success": True, "data": incident_data}

        except Exception as e:
            return {"error": f"Failed to upload to Firestore: {str(e)}"}
