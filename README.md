# openHASP Designer for Home Assistant

A modern, intuitive designer for creating openHASP touchscreen interfaces with deep Home Assistant integration.

## Features

- 🎨 **Visual Designer** - Drag-and-drop interface builder
- 🏠 **HA Integration** - Browse and select entities directly from Home Assistant
- 📱 **Multi-Device Support** - Works with any openHASP device (Lanbon L8, WT32-SC01, etc.)
- 🚀 **One-Click Deploy** - Deploy configurations directly to your devices
- 📥 **Import/Export** - Import existing configs from HA, export to JSONL
- ✅ **Validation** - Real-time validation of entities, coordinates, and device compatibility
- 🔄 **Live Preview** - See entity states on your design canvas

## Quick Start

### Installation (Home Assistant Add-on)

1. Add this repository to your Home Assistant add-on store:
   ```
   https://github.com/ketronkowski/openHasp-designer-ha
   ```

2. Install the "openHASP Designer" add-on

3. Start the add-on and open the Web UI

### Local Development

**Backend:**
```bash
cd backend-python
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your HA_TOKEN
uvicorn app.main:app --reload --port 8080
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Tests:**
```bash
# Backend tests
cd backend-python
pytest

# Frontend tests
cd frontend
npm run test
```

## Architecture

```
openHasp-designer-ha/
├── backend-python/     # FastAPI backend
│   ├── app/
│   │   ├── models/     # Pydantic models
│   │   ├── services/   # Business logic
│   │   └── main.py     # FastAPI app
│   └── tests/          # Backend tests
├── frontend/           # Vue 3 frontend (coming soon)
├── addon/              # HA add-on configuration (coming soon)
└── Dockerfile          # Multi-stage build
```

## Technology Stack

- **Backend:** Python 3.11, FastAPI, Pydantic
- **Frontend:** Vue 3, Vite, TypeScript (planned)
- **Testing:** pytest, Vitest, Playwright
- **Deployment:** Docker, Home Assistant Add-on

## Documentation

- [Product Requirements](docs/product_requirements.md)
- [Development Guide](docs/development_testing_guide.md)
- [Testing Guide](docs/testing_guide.md)
- [FAQ](docs/faq.md)

## License

- **Backend & Integration Code:** Apache 2.0
- **Frontend (OpenHaspDesigner fork):** MIT (see frontend/LICENSE)

## Credits

This project builds upon the excellent [OpenHaspDesigner](https://github.com/HASwitchPlate/openHASP-custom-component) by the openHASP team. The frontend designer is a fork with enhanced Home Assistant integration.

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

- [GitHub Issues](https://github.com/ketronkowski/openHasp-designer-ha/issues)
- [Home Assistant Community](https://community.home-assistant.io/)
