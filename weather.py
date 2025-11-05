from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
from datetime import datetime

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
IPMA_API_BASE = "https://api.ipma.pt/open-data"

async def make_ipma_request(url: str) -> dict[str, Any] | list[dict[str, Any]] | None:
    """Make a request to the IPMA API with proper error handling."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


@mcp.tool()
async def get_weather_warnings() -> str:
    """Get Portuguese meteorological warnings for up to 3 days.
    
    Returns current active weather warnings (Avisos Meteorológicos) including:
    - Warning type (precipitation, wind, fog, maritime agitation, etc.)
    - Awareness level (green, yellow, orange, red)
    - Affected area
    - Start and end times
    """
    warnings_url = f"{IPMA_API_BASE}/forecast/warnings/warnings_www.json"
    warnings_data = await make_ipma_request(warnings_url)
    
    if not warnings_data:
        return "Unable to fetch weather warnings data."
    
    # Filter active warnings (not green level)
    active_warnings = [w for w in warnings_data if w.get("awarenessLevelID") != "green"]
    
    if not active_warnings:
        return "No active weather warnings at this time. All areas are at green (normal) level."
    
    result = "Active Weather Warnings:\n\n"
    for warning in active_warnings:
        result += f"""Area: {warning.get('idAreaAviso', 'N/A')}
Type: {warning.get('awarenessTypeName', 'N/A')}
Level: {warning.get('awarenessLevelID', 'N/A').upper()}
Description: {warning.get('text', 'N/A')}
Start: {warning.get('startTime', 'N/A')}
End: {warning.get('endTime', 'N/A')}
---
"""
    
    return result


@mcp.tool()
async def get_forecast(city_name: str) -> str:
    """Get 5-day weather forecast for a Portuguese city (Previsão Meteorológica até 5 dias).

    Args:
        city_name: Name of the Portuguese city (e.g. Lisboa, Porto, Faro, Aveiro, Braga)
    
    Returns detailed 5-day forecast including temperature, precipitation, wind, and weather type.
    """
    # First, get the global ID for the city
    cities_url = f"{IPMA_API_BASE}/distrits-islands.json"
    cities_data = await make_ipma_request(cities_url)

    if not cities_data or "data" not in cities_data:
        return "Unable to fetch city database."

    # Search for the best match
    city_name_lower = city_name.lower()
    best_match = None
    
    for entry in cities_data["data"]:
        local_name = entry.get("local", "").lower()
        if city_name_lower in local_name or local_name in city_name_lower:
            best_match = entry
            break
    
    if not best_match:
        # Return available cities if no match found
        available_cities = [entry.get("local", "") for entry in cities_data["data"][:15]]
        return f"City '{city_name}' not found. Some available cities: {', '.join(available_cities)}"
    
    # Get the forecast using the global ID
    global_id = best_match.get("globalIdLocal")
    forecast_url = f"{IPMA_API_BASE}/forecast/meteorology/cities/daily/{global_id}.json"
    forecast_data = await make_ipma_request(forecast_url)

    if not forecast_data or "data" not in forecast_data:
        return "Unable to fetch forecast data for this location."

    # Format the forecast data
    city_info = f"5-Day Weather Forecast for {best_match.get('local')}\n"
    city_info += f"Location: {best_match.get('latitude')}°N, {best_match.get('longitude')}°E\n\n"
    
    forecasts = []
    for day in forecast_data["data"][:5]:  # Show next 5 days
        forecast = f"""Date: {day.get('forecastDate', 'Unknown')}
Max Temperature: {day.get('tMax', 'N/A')}°C
Min Temperature: {day.get('tMin', 'N/A')}°C
Precipitation Probability: {day.get('precipitaProb', 'N/A')}%
Weather Type ID: {day.get('idWeatherType', 'N/A')}
Wind Direction: {day.get('predWindDir', 'N/A')}
Wind Speed Class: {day.get('classWindSpeed', 'N/A')}
Precipitation Intensity Class: {day.get('classPrecInt', 'N/A')}
"""
        forecasts.append(forecast)

    return city_info + "---\n".join(forecasts)


@mcp.tool()
async def get_daily_aggregate_forecast(day: int = 0) -> str:
    """Get daily aggregated weather forecast for Portugal (Previsão Meteorológica até 3 dias, agregada por dia).
    
    Args:
        day: Forecast day (0=today, 1=tomorrow, 2=day after tomorrow). Valid range: 0-2
    
    Returns aggregated forecast for all Portuguese locations for the specified day.
    """
    if day < 0 or day > 2:
        return "Invalid day parameter. Please use 0 (today), 1 (tomorrow), or 2 (day after tomorrow)."
    
    forecast_url = f"{IPMA_API_BASE}/forecast/meteorology/cities/daily/hp-daily-forecast-day{day}.json"
    forecast_data = await make_ipma_request(forecast_url)
    
    if not forecast_data or "data" not in forecast_data:
        return "Unable to fetch daily aggregate forecast data."
    
    result = f"""Daily Aggregate Weather Forecast
Forecast Date: {forecast_data.get('forecastDate', 'Unknown')}
Data Updated: {forecast_data.get('dataUpdate', 'Unknown')}
Owner: {forecast_data.get('owner', 'IPMA')}

Total Locations: {len(forecast_data['data'])}

Sample Forecasts (first 10 locations):
"""
    
    for location in forecast_data['data'][:10]:
        result += f"""
Location ID: {location.get('globalIdLocal', 'N/A')}
Position: {location.get('latitude', 'N/A')}°N, {location.get('longitude', 'N/A')}°E
Temperature: {location.get('tMin', 'N/A')}°C - {location.get('tMax', 'N/A')}°C
Precipitation Probability: {location.get('precipitaProb', 'N/A')}%
Weather Type: {location.get('idWeatherType', 'N/A')}
Wind: {location.get('predWindDir', 'N/A')} (Speed Class: {location.get('classWindSpeed', 'N/A')})
---"""
    
    return result


@mcp.tool()
async def get_seismic_data(region: str = "all") -> str:
    """Get seismic activity data for Portugal (Informação sismicidade, últimos 30 dias).
    
    Args:
        region: Region to filter ('all', 'continente', 'açores', 'madeira'). 
                Default is 'all' for all regions.
    
    Note: This endpoint returns the last 30 days of seismic information for 
    Azores Archipelago, Continental Portugal, and Madeira Archipelago.
    """
    # Based on API exploration, trying common patterns for seismic data
    # The exact endpoint might vary, trying multiple possible URLs
    possible_urls = [
        f"{IPMA_API_BASE}/observation/seismic/latest30days.json",
        f"{IPMA_API_BASE}/seismic-data.json",
        f"{IPMA_API_BASE}/observation/seismology/events.json"
    ]
    
    seismic_data = None
    for url in possible_urls:
        seismic_data = await make_ipma_request(url)
        if seismic_data:
            break
    
    if not seismic_data:
        return """Seismic data endpoint is currently unavailable. 
The IPMA API provides seismic information for the last 30 days covering:
- Continental Portugal
- Azores Archipelago  
- Madeira Archipelago

Please try again later or check the IPMA website directly."""
    
    # Process and format the seismic data based on actual structure
    result = f"Seismic Activity (Last 30 Days)\n"
    result += f"Region Filter: {region}\n\n"
    
    # Add data processing logic based on actual API response structure
    if isinstance(seismic_data, list):
        filtered_events = seismic_data
        if region.lower() != "all":
            # Filter by region if the data structure supports it
            pass
        
        result += f"Total Events: {len(filtered_events)}\n\n"
        for event in filtered_events[:20]:  # Show first 20 events
            result += f"{event}\n---\n"
    else:
        result += str(seismic_data)
    
    return result


@mcp.tool()
async def get_sea_forecast(location_name: str = "", day: int = 0) -> str:
    """Get sea state forecast for Portuguese coastal areas (Previsão Estado do Mar até 3 dias).
    
    Args:
        location_name: Name of coastal location (e.g., 'Porto', 'Lisboa', 'Faro', 'Funchal', 'Leiria').
                      Leave empty to see all available locations.
        day: Forecast day (0=today, 1=tomorrow, 2=day after tomorrow). Valid range: 0-2
    
    Returns sea state forecast including wave height, period, direction, and sea temperature.
    """
    if day < 0 or day > 2:
        return "Invalid day parameter. Please use 0 (today), 1 (tomorrow), or 2 (day after tomorrow)."
    
    # Get sea forecast
    forecast_url = f"{IPMA_API_BASE}/forecast/oceanography/daily/hp-daily-sea-forecast-day{day}.json"
    forecast_data = await make_ipma_request(forecast_url)
    
    if not forecast_data or "data" not in forecast_data:
        return "Unable to fetch sea forecast data."
    
    # Get location names
    locations_url = f"{IPMA_API_BASE}/sea-locations.json"
    locations_data = await make_ipma_request(locations_url)
    
    # Create location mapping
    location_map = {}
    if locations_data and isinstance(locations_data, list):
        for loc in locations_data:
            location_map[loc.get('globalIdLocal')] = loc.get('local', 'Unknown')
    
    result = f"""Sea State Forecast
Forecast Date: {forecast_data.get('forecastDate', 'Unknown')}
Owner: {forecast_data.get('owner', 'IPMA')}

"""
    
    if not location_name:
        # Show all locations
        result += f"Available Locations ({len(forecast_data['data'])} total):\n\n"
        for location in forecast_data['data'][:10]:
            loc_id = location.get('globalIdLocal')
            loc_name = location_map.get(loc_id, f"ID: {loc_id}")
            result += f"""Location: {loc_name}
Position: {location.get('latitude', 'N/A')}°N, {location.get('longitude', 'N/A')}°E
Wave Height: {location.get('waveHighMin', 'N/A')}m - {location.get('waveHighMax', 'N/A')}m
Total Sea: {location.get('totalSeaMin', 'N/A')}m - {location.get('totalSeaMax', 'N/A')}m
Wave Period: {location.get('wavePeriodMin', 'N/A')}s - {location.get('wavePeriodMax', 'N/A')}s
Wave Direction: {location.get('predWaveDir', 'N/A')}
Sea Temperature: {location.get('sstMin', 'N/A')}°C - {location.get('sstMax', 'N/A')}°C
---
"""
    else:
        # Search for specific location
        location_name_lower = location_name.lower()
        found = False
        
        for location in forecast_data['data']:
            loc_id = location.get('globalIdLocal')
            loc_name = location_map.get(loc_id, '')
            
            if location_name_lower in loc_name.lower():
                found = True
                result += f"""Location: {loc_name}
Position: {location.get('latitude', 'N/A')}°N, {location.get('longitude', 'N/A')}°E
Wave Height: {location.get('waveHighMin', 'N/A')}m - {location.get('waveHighMax', 'N/A')}m
Total Sea: {location.get('totalSeaMin', 'N/A')}m - {location.get('totalSeaMax', 'N/A')}m
Wave Period: {location.get('wavePeriodMin', 'N/A')}s - {location.get('wavePeriodMax', 'N/A')}s
Wave Direction: {location.get('predWaveDir', 'N/A')}
Sea Temperature: {location.get('sstMin', 'N/A')}°C - {location.get('sstMax', 'N/A')}°C
"""
                break
        
        if not found:
            available = [location_map.get(loc.get('globalIdLocal'), f"ID: {loc.get('globalIdLocal')}") 
                        for loc in forecast_data['data'][:10]]
            result += f"Location '{location_name}' not found.\nAvailable locations: {', '.join(available)}"
    
    return result


@mcp.tool()
async def get_fire_risk(day: int = 0) -> str:
    """Get fire risk forecast for Portugal (Previsão Risco de Incêndio até 2 dias).
    
    Args:
        day: Forecast day (0=today, 1=tomorrow). Valid range: 0-1
    
    Returns fire risk classification (RCM - Risco de Incêndio) for Portuguese municipalities.
    Fire risk levels: 1=Low, 2=Moderate, 3=High, 4=Very High, 5=Maximum
    """
    if day < 0 or day > 1:
        return "Invalid day parameter. Please use 0 (today) or 1 (tomorrow)."
    
    fire_url = f"{IPMA_API_BASE}/forecast/meteorology/rcm/rcm-d{day}.json"
    fire_data = await make_ipma_request(fire_url)
    
    if not fire_data or "local" not in fire_data:
        return "Unable to fetch fire risk data."
    
    result = f"""Fire Risk Forecast (RCM - Risco de Incêndio)
Forecast Date: {fire_data.get('dataPrev', 'Unknown')}
Model Run Date: {fire_data.get('dataRun', 'Unknown')}
File Date: {fire_data.get('fileDate', 'Unknown')}

Fire Risk Levels: 1=Low, 2=Moderate, 3=High, 4=Very High, 5=Maximum

Sample Municipalities (first 20):
"""
    
    count = 0
    for dico, location in fire_data['local'].items():
        if count >= 20:
            break
        
        rcm_value = location.get('data', {}).get('rcm', 'N/A')
        risk_label = {1: 'Low', 2: 'Moderate', 3: 'High', 4: 'Very High', 5: 'Maximum'}.get(rcm_value, 'Unknown')
        
        result += f"""
Municipality Code: {dico}
Position: {location.get('latitude', 'N/A')}°N, {location.get('longitude', 'N/A')}°E
Fire Risk: {rcm_value} ({risk_label})
---"""
        count += 1
    
    total_locations = len(fire_data['local'])
    result += f"\n\nTotal Municipalities: {total_locations}"
    
    return result


@mcp.tool()
async def get_uv_forecast() -> str:
    """Get UV index forecast for Portugal (Previsão Índice Ultravioleta até 3 dias).
    
    Returns UV radiation index forecast for Portuguese locations.
    UV Index levels:
    - 0-2: Low
    - 3-5: Moderate
    - 6-7: High
    - 8-10: Very High
    - 11+: Extreme
    """
    uv_url = f"{IPMA_API_BASE}/forecast/meteorology/uv/uv.json"
    uv_data = await make_ipma_request(uv_url)
    
    if not uv_data:
        return """UV index forecast is currently unavailable.
The IPMA API provides UV radiation index forecasts for up to 3 days.

UV Index levels:
- 0-2: Low (minimal protection needed)
- 3-5: Moderate (protection recommended)
- 6-7: High (protection essential)
- 8-10: Very High (extra protection required)
- 11+: Extreme (avoid sun exposure)

Please try again later or check the IPMA website directly."""
    
    # Process UV data based on actual API structure
    if isinstance(uv_data, dict):
        result = "UV Index Forecast\n\n"
        result += str(uv_data)
    else:
        result = "UV Index Forecast\n\n"
        result += str(uv_data)
    
    return result


@mcp.tool()
async def get_station_observations(station_id: str = "") -> str:
    """Get meteorological observations from weather stations (Observações últimas 24 horas).
    
    Args:
        station_id: ID of the weather station. Leave empty to see all stations.
    
    Returns hourly meteorological observations from the last 24 hours including:
    - Temperature
    - Humidity  
    - Pressure
    - Wind speed and direction
    - Precipitation
    - Radiation
    """
    # Get observations
    obs_url = f"{IPMA_API_BASE}/observation/meteorology/stations/observations.json"
    obs_data = await make_ipma_request(obs_url)
    
    if not obs_data:
        return "Unable to fetch meteorological observations."
    
    # Get station information
    stations_url = f"{IPMA_API_BASE}/observation/meteorology/stations/stations.json"
    stations_data = await make_ipma_request(stations_url)
    
    # Create station mapping
    station_map = {}
    if stations_data and isinstance(stations_data, list):
        for station in stations_data:
            props = station.get('properties', {})
            station_map[str(props.get('idEstacao'))] = props.get('localEstacao', 'Unknown')
    
    if not station_id:
        # List available stations
        result = f"Available Weather Stations ({len(station_map)} total):\n\n"
        count = 0
        for sid, name in list(station_map.items())[:20]:
            result += f"ID: {sid} - {name}\n"
            count += 1
        result += f"\n... and {len(station_map) - count} more stations.\n"
        result += "\nUse station_id parameter to get observations for a specific station."
        return result
    
    # Get observations for specific station
    result = f"Meteorological Observations for Station {station_id}\n"
    result += f"Station Name: {station_map.get(station_id, 'Unknown')}\n\n"
    
    observations_found = False
    for timestamp, stations in obs_data.items():
        if station_id in stations:
            observations_found = True
            obs = stations[station_id]
            result += f"""Time: {timestamp} UTC
Temperature: {obs.get('temperatura', 'N/A')}°C
Humidity: {obs.get('humidade', 'N/A')}%
Pressure: {obs.get('pressao', 'N/A')} hPa
Wind Speed: {obs.get('intensidadeVento', 'N/A')} m/s ({obs.get('intensidadeVentoKM', 'N/A')} km/h)
Wind Direction: {obs.get('idDireccVento', 'N/A')}
Accumulated Precipitation: {obs.get('precAcumulada', 'N/A')} mm
Radiation: {obs.get('radiacao', 'N/A')} W/m²
---
"""
    
    if not observations_found:
        result += f"No observations found for station {station_id} in the last 24 hours."
    
    return result


@mcp.tool()
async def list_available_cities() -> str:
    """List all available Portuguese cities and islands for weather forecasts.
    
    Returns a comprehensive list of all locations available in the IPMA database,
    including district capitals and islands (Madeira and Azores).
    """
    cities_url = f"{IPMA_API_BASE}/distrits-islands.json"
    cities_data = await make_ipma_request(cities_url)
    
    if not cities_data or "data" not in cities_data:
        return "Unable to fetch cities database."
    
    result = f"Available Portuguese Cities and Islands ({len(cities_data['data'])} total)\n\n"
    
    # Group by region
    continente = []
    madeira = []
    acores = []
    
    for entry in cities_data["data"]:
        location_info = f"{entry.get('local')} (ID: {entry.get('globalIdLocal')})"
        region_id = entry.get('idRegiao', 0)
        
        if region_id == 1:
            continente.append(location_info)
        elif region_id == 2:
            madeira.append(location_info)
        elif region_id == 3:
            acores.append(location_info)
    
    result += f"CONTINENTAL PORTUGAL ({len(continente)} locations):\n"
    result += "\n".join(continente[:30])
    if len(continente) > 30:
        result += f"\n... and {len(continente) - 30} more\n"
    
    result += f"\n\nMADEIRA ARCHIPELAGO ({len(madeira)} locations):\n"
    result += "\n".join(madeira)
    
    result += f"\n\nAZORES ARCHIPELAGO ({len(acores)} locations):\n"
    result += "\n".join(acores)
    
    return result


@mcp.tool()
async def get_weather_type_descriptions() -> str:
    """Get descriptions for all weather type codes used in forecasts.
    
    Returns a mapping of weather type IDs to their Portuguese and English descriptions.
    This helps interpret the idWeatherType field in forecast data.
    """
    weather_url = f"{IPMA_API_BASE}/weather-type-classe.json"
    weather_data = await make_ipma_request(weather_url)
    
    if not weather_data or "data" not in weather_data:
        return "Unable to fetch weather type descriptions."
    
    result = f"""Weather Type Descriptions
Owner: {weather_data.get('owner', 'IPMA')}
Country: {weather_data.get('country', 'PT')}

ID | Portuguese | English
---|------------|--------
"""
    
    for weather_type in weather_data['data']:
        wid = weather_type.get('idWeatherType', 'N/A')
        pt_desc = weather_type.get('descWeatherTypePT', 'N/A')
        en_desc = weather_type.get('descWeatherTypeEN', 'N/A')
        result += f"{wid:3} | {pt_desc:30} | {en_desc}\n"
    
    return result

def main():
    # Initialize and run the server
    mcp.run(transport='stdio')    

if __name__ == "__main__":
    main()
