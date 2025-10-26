from google import genai
from google.genai import types
import json
from datetime import datetime
from pydantic import BaseModel

# Initialize Gemini Client (your key should be in the environment)

client = genai.Client()
class Location(BaseModel):
    lat: float
    lng: float

class CustomResponseSchema(BaseModel):
    category: str
    summary: str
    severity: str
    location: Location
    timestamp: str
    image_url: str
    area: str
    zipcode: str
    
# ====== 🔁 SIMULATED STATIC GPS DATA ======
user_lat = 12.9121
user_lng = 77.6446
area = "HSR Layout"
image_url = "https://image.firebase.com/flood123.jpg"  # Replace later after Firebase upload

# ====== 🖼️ LOAD IMAGE ======
with open('stampede.jpeg', 'rb') as f:
    image_bytes = f.read()

# ====== 🧠 SMART PROMPT FOR AGENTIC CITY AWARENESS ======
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
  "location": {{ "lat": 12.9121, "lng": 77.6446 }},
  "timestamp": "{datetime.utcnow().isoformat()}Z",
  "image_url": "https://image.firebase.com/incident_xxx.jpg",
  "area": "...",
  "zipcode": "..."
}}
If the event involves a large crowd, fallen shoes, or chaos, categorize it as "Stampede" or "Flash Mob" depending on the situation. Avoid vague terms like "Other" unless absolutely nothing fits.
"""

# ====== 🤖 GEMINI API CALL ======
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
        prompt
    ],
    config={
        "response_mime_type": "application/json",
        "response_schema": CustomResponseSchema.model_json_schema(),
    }
)

try:
    print("\n✅ Parsed JSON:\n")
    structured_data = response.parsed
    print(structured_data)
except json.JSONDecodeError as e:
    print("\n❌ Failed to parse JSON:\n", e)
