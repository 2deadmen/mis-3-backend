from fastapi import APIRouter, UploadFile, File, Form
from google import genai
from ai_helpers.gemini import GeminiCityAnalyzer
from ai_helpers.gemini2 import GeminiCityDataGetter
from geopy.distance import geodesic
from typing import List
from fastapi import Query
from pydantic import BaseModel
router = APIRouter()
analyzer = GeminiCityAnalyzer()


class IncidentInput(BaseModel):
    lat: float
    lng: float
    image_url: str
    area: str


#curl http://127.0.0.1:8000/data/get_data
@router.get("/get_data")
async def get_data_endpoint():
    """
    Handles GET requests to retrieve data.
    """
    return {"message": "This is your GET data endpoint!"}




# curl -X POST http://127.0.0.1:8000/data/incident/report \
# -H "Content-Type: application/json" \
# -d '{
# "lat": 12.9121,
# "lng": 77.6446,
# "area": "HSR Layout",
# "image_url": "https://picsum.photos/200/300"
#   }'

@router.post("/incident/report")
async def report_incident(payload: IncidentInput):
    result = analyzer.analyze_incident(
        image_url=payload.image_url,
        lat=payload.lat,
        lng=payload.lng,
        area=payload.area
    )
    return result

@router.get("/get_incidents_by_route")
async def get_incidents_by_route(
    source_lat: float,
    source_lng: float,
    dest_lat: float,
    dest_lng: float
):
    try:
        getter = GeminiCityDataGetter()
        incidents = getter.get_incidents_along_route(source_lat, source_lng, dest_lat, dest_lng)
        return {"incidents": incidents}
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        return {"error": str(e), "trace": traceback_str}