import time
import requests
from typing import Dict, Any, Optional

# WMO Weather interpretation codes (WW)
WMO_CODE_MAP = {
    0: ("Clear sky", "clear"),
    1: ("Mainly clear", "mostly-clear"),
    2: ("Partly cloudy", "partly-cloudy"),
    3: ("Overcast", "overcast"),
    45: ("Foggy", "fog"),
    48: ("Depositing rime fog", "fog"),
    51: ("Light drizzle", "drizzle"),
    53: ("Moderate drizzle", "drizzle"),
    55: ("Dense drizzle", "drizzle"),
    61: ("Slight rain", "rain"),
    63: ("Moderate rain", "rain"),
    65: ("Heavy rain", "heavy-rain"),
    71: ("Slight snow fall", "snow"),
    73: ("Moderate snow fall", "snow"),
    75: ("Heavy snow fall", "snow"),
    77: ("Snow grains", "snow"),
    80: ("Slight rain showers", "rain-showers"),
    81: ("Moderate rain showers", "rain-showers"),
    82: ("Violent rain showers", "heavy-rain"),
    85: ("Slight snow showers", "snow"),
    86: ("Heavy snow showers", "snow"),
    95: ("Thunderstorm", "thunderstorm"),
    96: ("Thunderstorm with slight hail", "thunderstorm"),
    99: ("Thunderstorm with heavy hail", "thunderstorm"),
}

CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes cache

FALLBACK_CITIES = {
    "london": {
        "city": "London",
        "country": "United Kingdom",
        "temp_c": 16.5,
        "feels_like_c": 15.2,
        "condition": "Partly cloudy",
        "icon": "partly-cloudy",
        "humidity": 68,
        "wind_kph": 18.0,
        "pressure_mb": 1014,
        "visibility_km": 10.0,
        "uv_index": 4.2,
        "forecast": [
            {"day": "Mon", "condition": "Partly cloudy", "icon": "partly-cloudy", "high_c": 18, "low_c": 11, "precip_mm": 0.2},
            {"day": "Tue", "condition": "Light rain", "icon": "rain", "high_c": 15, "low_c": 10, "precip_mm": 4.1},
            {"day": "Wed", "condition": "Overcast", "icon": "overcast", "high_c": 16, "low_c": 9, "precip_mm": 0.0},
            {"day": "Thu", "condition": "Mainly clear", "icon": "mostly-clear", "high_c": 19, "low_c": 12, "precip_mm": 0.0},
            {"day": "Fri", "condition": "Clear sky", "icon": "clear", "high_c": 21, "low_c": 13, "precip_mm": 0.0},
        ]
    },
    "pune": {
        "city": "Pune",
        "country": "India",
        "temp_c": 28.0,
        "feels_like_c": 29.5,
        "condition": "Mainly clear",
        "icon": "mostly-clear",
        "humidity": 52,
        "wind_kph": 12.0,
        "pressure_mb": 1011,
        "visibility_km": 9.5,
        "uv_index": 8.0,
        "forecast": [
            {"day": "Mon", "condition": "Mainly clear", "icon": "mostly-clear", "high_c": 31, "low_c": 21, "precip_mm": 0.0},
            {"day": "Tue", "condition": "Clear sky", "icon": "clear", "high_c": 32, "low_c": 22, "precip_mm": 0.0},
            {"day": "Wed", "condition": "Partly cloudy", "icon": "partly-cloudy", "high_c": 30, "low_c": 20, "precip_mm": 0.0},
            {"day": "Thu", "condition": "Slight rain showers", "icon": "rain-showers", "high_c": 29, "low_c": 21, "precip_mm": 2.5},
            {"day": "Fri", "condition": "Mainly clear", "icon": "mostly-clear", "high_c": 31, "low_c": 21, "precip_mm": 0.0},
        ]
    },
    "mumbai": {
        "city": "Mumbai",
        "country": "India",
        "temp_c": 31.0,
        "feels_like_c": 35.0,
        "condition": "Hazy & Warm",
        "icon": "partly-cloudy",
        "humidity": 75,
        "wind_kph": 15.0,
        "pressure_mb": 1009,
        "visibility_km": 7.0,
        "uv_index": 7.5,
        "forecast": [
            {"day": "Mon", "condition": "Partly cloudy", "icon": "partly-cloudy", "high_c": 32, "low_c": 26, "precip_mm": 0.0},
            {"day": "Tue", "condition": "Partly cloudy", "icon": "partly-cloudy", "high_c": 33, "low_c": 26, "precip_mm": 0.0},
            {"day": "Wed", "condition": "Mainly clear", "icon": "mostly-clear", "high_c": 32, "low_c": 25, "precip_mm": 0.0},
            {"day": "Thu", "condition": "Clear sky", "icon": "clear", "high_c": 33, "low_c": 26, "precip_mm": 0.0},
            {"day": "Fri", "condition": "Partly cloudy", "icon": "partly-cloudy", "high_c": 32, "low_c": 25, "precip_mm": 0.0},
        ]
    },
    "new york": {
        "city": "New York",
        "country": "United States",
        "temp_c": 19.0,
        "feels_like_c": 18.5,
        "condition": "Clear sky",
        "icon": "clear",
        "humidity": 55,
        "wind_kph": 14.0,
        "pressure_mb": 1018,
        "visibility_km": 12.0,
        "uv_index": 5.0,
        "forecast": [
            {"day": "Mon", "condition": "Clear sky", "icon": "clear", "high_c": 21, "low_c": 13, "precip_mm": 0.0},
            {"day": "Tue", "condition": "Partly cloudy", "icon": "partly-cloudy", "high_c": 20, "low_c": 14, "precip_mm": 0.0},
            {"day": "Wed", "condition": "Slight rain", "icon": "rain", "high_c": 17, "low_c": 12, "precip_mm": 5.0},
            {"day": "Thu", "condition": "Overcast", "icon": "overcast", "high_c": 18, "low_c": 11, "precip_mm": 0.5},
            {"day": "Fri", "condition": "Mainly clear", "icon": "mostly-clear", "high_c": 22, "low_c": 14, "precip_mm": 0.0},
        ]
    },
    "tokyo": {
        "city": "Tokyo",
        "country": "Japan",
        "temp_c": 20.5,
        "feels_like_c": 20.0,
        "condition": "Mainly clear",
        "icon": "mostly-clear",
        "humidity": 60,
        "wind_kph": 10.0,
        "pressure_mb": 1016,
        "visibility_km": 10.0,
        "uv_index": 5.5,
        "forecast": [
            {"day": "Mon", "condition": "Mainly clear", "icon": "mostly-clear", "high_c": 22, "low_c": 15, "precip_mm": 0.0},
            {"day": "Tue", "condition": "Clear sky", "icon": "clear", "high_c": 23, "low_c": 16, "precip_mm": 0.0},
            {"day": "Wed", "condition": "Slight rain", "icon": "rain", "high_c": 19, "low_c": 14, "precip_mm": 3.0},
            {"day": "Thu", "condition": "Partly cloudy", "icon": "partly-cloudy", "high_c": 21, "low_c": 15, "precip_mm": 0.0},
            {"day": "Fri", "condition": "Mainly clear", "icon": "mostly-clear", "high_c": 22, "low_c": 15, "precip_mm": 0.0},
        ]
    }
}


def c_to_f(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return round((celsius * 9 / 5) + 32, 1)


def kph_to_mph(kph: float) -> float:
    """Convert km/h to mph."""
    return round(kph * 0.621371, 1)


def mm_to_inches(mm: float) -> float:
    """Convert mm to inches."""
    return round(mm * 0.0393701, 2)


def get_cached_weather(city_key: str) -> Optional[Dict[str, Any]]:
    if city_key in CACHE:
        cached_entry = CACHE[city_key]
        if time.time() - cached_entry["timestamp"] < CACHE_TTL_SECONDS:
            return cached_entry["data"]
    return None


def set_cached_weather(city_key: str, data: Dict[str, Any]):
    CACHE[city_key] = {
        "timestamp": time.time(),
        "data": data
    }


def generate_generic_fallback(city_name: str) -> Dict[str, Any]:
    """Generates deterministic mock data for arbitrary cities when offline."""
    seed = sum(ord(c) for c in city_name)
    base_temp = 15.0 + (seed % 16)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    forecast = []
    for i, d in enumerate(days):
        day_temp = base_temp + ((seed * (i + 1)) % 7) - 3
        forecast.append({
            "day": d,
            "condition": "Partly cloudy",
            "icon": "partly-cloudy",
            "high_c": round(day_temp + 3, 1),
            "low_c": round(day_temp - 4, 1),
            "precip_mm": round((seed % 4) * 0.5, 1)
        })

    return {
        "city": city_name.strip().title(),
        "country": "Region",
        "temp_c": round(base_temp, 1),
        "feels_like_c": round(base_temp - 0.5, 1),
        "condition": "Partly cloudy",
        "icon": "partly-cloudy",
        "humidity": 50 + (seed % 35),
        "wind_kph": 10.0 + (seed % 15),
        "pressure_mb": 1012,
        "visibility_km": 10.0,
        "uv_index": 5.0,
        "forecast": forecast,
        "source": "fallback-offline"
    }


def fetch_weather_data(city_name: str) -> Dict[str, Any]:
    """
    Fetches real-time weather data for a city using Open-Meteo (no API key required).
    Falls back gracefully to rich static data on network failure or rate limit.
    """
    clean_name = city_name.strip().lower()
    if not clean_name:
        clean_name = "pune"

    cached = get_cached_weather(clean_name)
    if cached:
        return cached

    # Attempt Live API
    try:
        # Step 1: Geocode city name
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.quote(clean_name)}&count=1&language=en&format=json"
        geo_res = requests.get(geo_url, timeout=3.0)

        if geo_res.status_code == 200:
            geo_data = geo_res.json()
            results = geo_data.get("results")
            if results and len(results) > 0:
                loc = results[0]
                lat = loc.get("latitude")
                lon = loc.get("longitude")
                resolved_city = loc.get("name", city_name.title())
                resolved_country = loc.get("country", "")

                # Step 2: Fetch weather forecast
                weather_url = (
                    f"https://api.open-meteo.com/v1/forecast?"
                    f"latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,"
                    f"apparent_temperature,is_day,precipitation,weather_code,surface_pressure,wind_speed_10m&"
                    f"daily=weather_code,temperature_2m_max,temperature_2m_min,uv_index_max,precipitation_sum&"
                    f"timezone=auto"
                )
                w_res = requests.get(weather_url, timeout=3.5)
                if w_res.status_code == 200:
                    w_data = w_res.json()
                    current = w_data.get("current", {})
                    daily = w_data.get("daily", {})

                    w_code = current.get("weather_code", 0)
                    condition_text, icon_name = WMO_CODE_MAP.get(w_code, ("Clear sky", "clear"))

                    daily_times = daily.get("time", [])[:5]
                    daily_codes = daily.get("weather_code", [])[:5]
                    daily_max = daily.get("temperature_2m_max", [])[:5]
                    daily_min = daily.get("temperature_2m_min", [])[:5]
                    daily_precip = daily.get("precipitation_sum", [])[:5]

                    forecast_list = []
                    for i, t in enumerate(daily_times):
                        c_code = daily_codes[i] if i < len(daily_codes) else 0
                        c_cond, c_icon = WMO_CODE_MAP.get(c_code, ("Clear", "clear"))
                        # extract weekday from yyyy-mm-dd
                        try:
                            day_label = time.strftime("%a", time.strptime(t, "%Y-%m-%d"))
                        except Exception:
                            day_label = f"Day {i+1}"

                        forecast_list.append({
                            "day": day_label,
                            "condition": c_cond,
                            "icon": c_icon,
                            "high_c": round(daily_max[i], 1) if i < len(daily_max) else 25.0,
                            "low_c": round(daily_min[i], 1) if i < len(daily_min) else 15.0,
                            "precip_mm": round(daily_precip[i], 1) if i < len(daily_precip) else 0.0,
                        })

                    result_data = {
                        "city": resolved_city,
                        "country": resolved_country,
                        "temp_c": round(current.get("temperature_2m", 20.0), 1),
                        "feels_like_c": round(current.get("apparent_temperature", 20.0), 1),
                        "condition": condition_text,
                        "icon": icon_name,
                        "humidity": current.get("relative_humidity_2m", 50),
                        "wind_kph": round(current.get("wind_speed_10m", 10.0), 1),
                        "pressure_mb": round(current.get("surface_pressure", 1013.0)),
                        "visibility_km": 10.0,
                        "uv_index": round(daily.get("uv_index_max", [5.0])[0], 1) if daily.get("uv_index_max") else 5.0,
                        "forecast": forecast_list,
                        "source": "live-api"
                    }
                    set_cached_weather(clean_name, result_data)
                    return result_data
    except Exception:
        # Silently fall back to cached or deterministic mock data
        pass

    # Fallback to curated dictionary if available
    if clean_name in FALLBACK_CITIES:
        fallback_data = dict(FALLBACK_CITIES[clean_name])
        fallback_data["source"] = "curated-fallback"
        set_cached_weather(clean_name, fallback_data)
        return fallback_data

    # Otherwise synthesize realistic data
    gen_data = generate_generic_fallback(clean_name)
    set_cached_weather(clean_name, gen_data)
    return gen_data


def format_weather_response(raw_data: Dict[str, Any], units: str = "metric") -> Dict[str, Any]:
    """Formats weather response for metric (Celsius, km/h) or imperial (Fahrenheit, mph)."""
    is_imperial = (units.lower() == "imperial")
    
    temp = c_to_f(raw_data["temp_c"]) if is_imperial else raw_data["temp_c"]
    feels_like = c_to_f(raw_data["feels_like_c"]) if is_imperial else raw_data["feels_like_c"]
    wind = kph_to_mph(raw_data["wind_kph"]) if is_imperial else raw_data["wind_kph"]
    wind_unit = "mph" if is_imperial else "km/h"
    temp_unit = "°F" if is_imperial else "°C"
    
    formatted_forecast = []
    for f in raw_data.get("forecast", []):
        high = c_to_f(f["high_c"]) if is_imperial else f["high_c"]
        low = c_to_f(f["low_c"]) if is_imperial else f["low_c"]
        precip = mm_to_inches(f["precip_mm"]) if is_imperial else f["precip_mm"]
        precip_unit = "in" if is_imperial else "mm"
        
        formatted_forecast.append({
            "day": f["day"],
            "condition": f["condition"],
            "icon": f["icon"],
            "high": high,
            "low": low,
            "precip": precip,
            "precip_unit": precip_unit
        })

    return {
        "city": raw_data["city"],
        "country": raw_data["country"],
        "temp": temp,
        "temp_unit": temp_unit,
        "feels_like": feels_like,
        "condition": raw_data["condition"],
        "icon": raw_data["icon"],
        "humidity": raw_data["humidity"],
        "wind": wind,
        "wind_unit": wind_unit,
        "pressure": raw_data["pressure_mb"],
        "visibility": raw_data["visibility_km"],
        "uv_index": raw_data["uv_index"],
        "forecast": formatted_forecast,
        "units": "imperial" if is_imperial else "metric",
        "source": raw_data.get("source", "system")
    }
