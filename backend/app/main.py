from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import httpx

app = FastAPI(title="Atmosfera-Web API", version="0.1.0")

# Configure CORS to allow requests from the frontend during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables for API keys
OWM_API_KEY = os.environ.get("OWM_API_KEY")
OWM_GEOCODING_URL = "http://api.openweathermap.org/geo/1.0/direct"
OWM_ONECALL_URL = "https://api.openweathermap.org/data/3.0/onecall"
OPENAQ_BASE_URL = "https://api.openaq.org/v3"

@app.get("/api/search")
async def search(q: str, limit: int = 5):
    """Search for cities using the OpenWeatherMap Geocoding API."""
    if not OWM_API_KEY:
        raise HTTPException(status_code=500, detail="OWM_API_KEY is not configured")
    params = {"q": q, "limit": limit, "appid": OWM_API_KEY}
    async with httpx.AsyncClient() as client:
        resp = await client.get(OWM_GEOCODING_URL, params=params, timeout=10)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

@app.get("/api/weather")
async def get_weather(lat: float, lon: float, units: str = "metric"):
    """Get comprehensive weather data for the given coordinates.
    This endpoint proxies the One Call API v3 and can be extended to merge
    data from OpenAQ for air quality.
    """
    if not OWM_API_KEY:
        raise HTTPException(status_code=500, detail="OWM_API_KEY is not configured")
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OWM_API_KEY,
        "units": units,
    }
    async with httpx.AsyncClient() as client:
        weather_resp = await client.get(OWM_ONECALL_URL, params=params, timeout=10)
    if weather_resp.status_code != 200:
        raise HTTPException(status_code=weather_resp.status_code, detail=weather_resp.text)
    weather_data = weather_resp.json()

    # Placeholder for integrating OpenAQ data.
    # To implement: find nearest stations via OpenAQ and fetch latest measurements
    # Example:
    # aq_params = {"coordinates": f"{lat},{lon}", "radius": 12000, "limit": 5}
    # async with httpx.AsyncClient() as client:
    #     locations_resp = await client.get(f"{OPENAQ_BASE_URL}/locations", params=aq_params)
    #     ...

    return weather_data
