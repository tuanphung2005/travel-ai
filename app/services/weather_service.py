"""Service for fetching weather forecasts from OpenWeatherMap."""
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import httpx
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)

@dataclass
class DailyWeather:
    """Consolidated daily weather forecast."""
    date: date
    condition: str          # e.g. "Rain", "Clear", "Clouds" (maps to OWM main condition)
    description: str        # e.g. "light rain"
    temp_min_c: float
    temp_max_c: float
    rain_probability: float # 0.0 - 1.0 (from OWM "pop" field)
    icon: str               # OWM icon code


async def fetch_daily_weather(lat: float, lon: float, start_date: date, num_days: int) -> Optional[list[DailyWeather]]:
    """
    Fetch a 5-day / 3-hour forecast and consolidate it into daily summaries.
    Returns None if weather data cannot be fetched (e.g. absent API key or API error).
    """
    settings = get_settings()
    api_key = getattr(settings, "OPENWEATHERMAP_API_KEY", None)
    if not api_key:
        logger.warning("OPENWEATHERMAP_API_KEY is not set. Planner will run without weather info.")
        return None
        
    if num_days <= 0:
        return []

    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",
    }
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
        return _parse_owm_forecast(data, start_date, num_days)
        
    except Exception as e:
        logger.error(f"Failed to fetch weather data: {e}")
        return None

def _parse_owm_forecast(data: dict, start_date: date, num_days: int) -> list[DailyWeather]:
    """Parse OWM 3-hour forecast items into daily summaries."""
    daily_summaries = {}
    end_date = start_date + timedelta(days=num_days - 1)
    
    for item in data.get("list", []):
        dt_txt = item.get("dt_txt", "")
        if not dt_txt:
            continue
            
        try:
            item_date = datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S").date()
        except ValueError:
            continue
            
        if item_date < start_date or item_date > end_date:
            continue
            
        # Initialize or update daily summary
        if item_date not in daily_summaries:
            daily_summaries[item_date] = {
                "temps": [],
                "pops": [], # Probability of precipitation
                "conditions": [],
            }
            
        day_data = daily_summaries[item_date]
        main = item.get("main", {})
        weather = item.get("weather", [{}])[0]
        
        day_data["temps"].append(main.get("temp", 0))
        day_data["pops"].append(item.get("pop", 0))
        day_data["conditions"].append({
            "main": weather.get("main", "Clear"),
            "desc": weather.get("description", ""),
            "icon": weather.get("icon", ""),
            "id": weather.get("id", 800) # OWM weather condition id
        })
        
    # Consolidate
    result = []
    for d in sorted(daily_summaries.keys()):
        day_data = daily_summaries[d]
        temps = day_data["temps"]
        pops = day_data["pops"]
        conditions = day_data["conditions"]
        
        if not temps:
            continue
            
        # Determine primary condition
        # We prioritize Rain/Snow over Clouds if they appear during the day
        primary_cond = conditions[0]
        for c in conditions:
            # OWM IDs: 2xx Thunderstorm, 3xx Drizzle, 5xx Rain, 6xx Snow
            if c["id"] < 700: 
                primary_cond = c
                break
                
        # If it's technically rain but probability is extremely low, fallback might be needed, 
        # but usually OWM returns "Rain" main condition only if it expects it.
        max_pop = max(pops) if pops else 0.0
        
        result.append(DailyWeather(
            date=d,
            condition=primary_cond["main"],
            description=primary_cond["desc"],
            temp_min_c=round(min(temps), 1),
            temp_max_c=round(max(temps), 1),
            rain_probability=round(max_pop, 2),
            icon=primary_cond["icon"]
        ))
        
    return result
