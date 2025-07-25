import os
import asyncio
from datetime import datetime

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# API key for OpenWeatherMap One Call
OWM_API_KEY = os.getenv("OWM_API_KEY")

async def fetch_weather(lat: float, lon: float):
    """Fetch weather data from OpenWeatherMap for given coordinates."""
    url = "https://api.openweathermap.org/data/3.0/onecall"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OWM_API_KEY,
        "units": "metric",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # TODO: Normalize and store data to the database
        print(f"Fetched weather for {lat},{lon} at {datetime.utcnow()}")
        return data

async def scheduled_weather_job():
    """Scheduled job to fetch weather for a list of predefined locations."""
    # Example coordinates for demonstration (Cali, Bogotá)
    coords = [
        (3.4516, -76.5320),  # Cali
        (4.7110, -74.0721),  # Bogotá
    ]
    for lat, lon in coords:
        await fetch_weather(lat, lon)

async def main():
    """Entry point for the ingestion service."""
    scheduler = AsyncIOScheduler()
    # Schedule weather data collection every 30 minutes
    scheduler.add_job(scheduled_weather_job, trigger="interval", minutes=30)
    scheduler.start()
    print("Ingestion service scheduler started")
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    asyncio.run(main())
