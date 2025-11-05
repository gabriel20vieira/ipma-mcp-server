# IPMA Weather MCP Server (Python)

A comprehensive Model Context Protocol (MCP) server providing access to Portuguese weather data from IPMA (Instituto Português do Mar e da Atmosfera).

## Data Source

All data is provided by **IPMA** (Instituto Português do Mar e da Atmosfera, I.P.)

-   API Documentation: https://api.ipma.pt/
-   Weather forecasts are updated twice daily (00 UTC and 12 UTC)
-   Times are in UTC (add 0h in winter, +1h in summer for Continental Portugal/Madeira; -1h in winter, 0h in summer for Azores)

## Features

This MCP server provides complete access to the IPMA API with the following tools:

### 🌦️ Weather Forecasts

1. **get_forecast** - 5-day weather forecast for Portuguese cities

    - Detailed daily forecasts including temperature, precipitation, wind
    - Supports all Portuguese cities and islands (Madeira and Azores)

2. **get_daily_aggregate_forecast** - Daily aggregated forecast for all locations
    - Get forecasts for all Portugal in a single query
    - Supports up to 3 days (today, tomorrow, day after tomorrow)

### ⚠️ Weather Warnings

3. **get_weather_warnings** - Active meteorological warnings (up to 3 days)
    - Warning types: precipitation, wind, fog, maritime agitation, snow, thunderstorms, etc.
    - Awareness levels: green (normal), yellow, orange, red
    - Includes affected areas and time periods

### 🌊 Sea State

4. **get_sea_forecast** - Sea state forecast for coastal areas (up to 3 days)
    - Wave height, wave period, wave direction
    - Sea surface temperature
    - Covers all Portuguese coastal locations

### 🔥 Fire Risk

5. **get_fire_risk** - Fire risk forecast (up to 2 days)
    - RCM (Risco de Incêndio) classification for all municipalities
    - Risk levels: Low, Moderate, High, Very High, Maximum

### ☀️ UV Index

6. **get_uv_forecast** - UV radiation index forecast (up to 3 days)
    - UV index levels from Low to Extreme
    - Protection recommendations included

### 🌡️ Weather Stations

7. **get_station_observations** - Meteorological observations from weather stations
    - Last 24 hours of hourly data
    - Temperature, humidity, pressure, wind, precipitation, radiation

### 🔍 Seismic Data

8. **get_seismic_data** - Seismic activity information (last 30 days)
    - Coverage: Continental Portugal, Azores, Madeira
    - Filter by region

### 📚 Reference Data

9. **list_available_cities** - List all available locations

    - Complete list of cities and islands
    - Grouped by region (Continental, Madeira, Azores)

10. **get_weather_type_descriptions** - Weather type code descriptions
    - Portuguese and English descriptions
    - Helps interpret weather type IDs in forecasts

## Installation

1. Install dependencies:

```bash
pip install -e .
```

2. Configure your MCP client to use this server:

For Claude Desktop, add to your config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
    "mcpServers": {
        "weather": {
            "command": "python",
            "args": ["-m", "weather"],
            "cwd": "/path/to/weather-server-python"
        }
    }
}
```

Or use `uv` for better environment management:

```json
{
    "mcpServers": {
        "weather": {
            "command": "uv",
            "args": ["run", "weather"],
            "cwd": "/path/to/weather-server-python"
        }
    }
}
```

## Usage Examples

Once configured, you can ask Claude questions like:

-   "What's the weather forecast for Lisboa?"
-   "Are there any active weather warnings in Portugal?"
-   "What's the sea state forecast for Porto coast tomorrow?"
-   "Show me the fire risk for today"
-   "What are the UV levels for the next 3 days?"
-   "Get observations from weather station 1210881"
-   "List all available Portuguese cities"
-   "What seismic activity has been recorded in the Azores?"

## API Coverage

This server implements all main IPMA open data endpoints:

✅ Avisos Meteorológicos até 3 dias  
✅ Previsão Meteorológica Diária até 5 dias agregada por Local  
✅ Previsão Meteorológica Diária até 3 dias, informação agregada por dia  
✅ Informação sismicidade, últimos 30 dias (Açores, Continente, Madeira)  
✅ Previsão do Estado do Mar até 3 dias, informação agregada por dia  
✅ Previsão do Risco de Incêndio até 2 dias, informação agregada por dia  
✅ Previsão do Risco de Ultravioletas até 3 dias (Índice Ultravioleta)  
✅ Observação Meteorológica de Estações (dados horários, últimas 24 horas)

## Integrating with Open WebUI

The IPMA MCP server can be integrated with Open WebUI (v0.6+) using **mcpo** (MCP-to-OpenAPI proxy), which bridges the stdio-based MCP server to REST endpoints accessible by Open WebUI.

### Quick Start with install.sh

We provide an installation helper script to set up the environment:

```bash
# Make the script executable
chmod +x install.sh

# Run the installation
./install.sh
```

The script will:

-   Install `uv` if not already present
-   Create a virtual environment
-   Install all dependencies
-   Verify the installation

### Manual Setup

#### 1. **Prerequisites**

-   Open WebUI installed and running (e.g., via Docker):
    ```bash
    docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway \
      -v open-webui:/app/backend/data \
      -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
      --name open-webui --restart always \
      ghcr.io/open-webui/open-webui:main
    ```
-   Python 3.10+ with `uv` (install via `curl -LsSf https://astral.sh/uv/install.sh | sh`)
-   Clone this repository

#### 2. **Set Up Virtual Environment**

```bash
cd /path/to/ipma-mcp-server
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

#### 3. **Test the MCP Server**

Run the server directly (it uses stdio transport by default):

```bash
uv run python weather.py
```

This starts the MCP server locally. Press Ctrl+C to stop.

#### 4. **Launch mcpo Proxy**

Install mcpo (Open WebUI's official MCP-to-OpenAPI proxy):

```bash
uv tool install mcpo
```

Proxy the MCP server to OpenAPI on port 8000 (use a secure API key):

```bash
uvx mcpo --port 8000 --api-key "your-secret-key" -- uv run python weather.py
```

-   Test: Visit `http://localhost:8000/docs` for the auto-generated OpenAPI schema
-   All IPMA tools should appear in the documentation

**Docker Alternative:**

```bash
docker run -p 8000:8000 -v /path/to/ipma-mcp-server:/app \
  ghcr.io/open-webui/mcpo:main \
  --api-key "your-secret-key" -- python /app/weather.py
```

#### 5. **Add to Open WebUI**

-   Open your Open WebUI instance (e.g., `http://localhost:3000`)
-   Go to **Settings** (gear icon) > **Tools** (or Admin Panel > External Tools if admin)
-   Click **+ Add Tool Server**
-   Configure:
    -   **Type**: OpenAPI (or MCP Streamable HTTP if available)
    -   **URL**: `http://localhost:8000` (full base URL)
    -   **Auth**: Bearer token with your API key (`your-secret-key`)
-   Save and restart Open WebUI if prompted

### Integration Architecture

```
Open WebUI (Port 3000)
    ↓ HTTP REST calls
mcpo Proxy (Port 8000)
    ↓ stdio JSON-RPC
IPMA MCP Server (weather.py)
    ↓ HTTPS
IPMA API (api.ipma.pt)
```

For full MCP documentation, see the [Open WebUI MCP Guide](https://docs.openwebui.com/openapi-servers/mcp/).

## License

See the [Quickstart](https://modelcontextprotocol.io/quickstart) tutorial for more information about MCP.
