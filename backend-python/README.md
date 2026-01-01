# Python Backend for openHASP Designer

FastAPI-based backend providing Home Assistant integration for the openHASP Designer.

## Features

- Home Assistant entity browsing and search
- JSONL config generation and publishing
- Layout save/load functionality
- Import existing openHASP configurations
- Automatic page reload triggering

## Setup

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your HA URL and token

# Run development server
uvicorn app.main:app --reload --port 8080
```

### Environment Variables

- `HA_URL` - Home Assistant URL (default: https://ha-nh.tronkowski.org)
- `HA_TOKEN` - Long-lived access token from HA
- `HA_CONFIG_PATH` - Path to openHASP config directory (default: /config/openhasp)

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## API Endpoints

### Home Assistant
- `GET /api/ha/entities` - List/search entities
- `POST /api/ha/reload` - Trigger page reload

### Configuration
- `POST /api/config/publish` - Deploy config to HA
- `GET/POST /api/config/layout` - Quick save/load
- `GET/POST/DELETE /api/config/layouts/{id}` - Named layouts
- `GET /api/config/import/available` - List JSONL files
- `GET/POST /api/config/import` - Import from HA

### Status
- `GET /api/status` - Health check

## License

Apache 2.0 (backend code)

Frontend (OpenHaspDesigner fork) is MIT licensed - see frontend/LICENSE
