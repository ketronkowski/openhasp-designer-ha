# Local Development & Testing Guide for openHASP Designer Add-on

> [!NOTE]
> For answers to technical questions about openHASP integration, see [FAQ.md](file:///Users/kevin/.gemini/antigravity/brain/32471498-e5bf-4770-8b09-33368b1b242a/faq.md)

## Updated Product Requirements

### Multi-Device Support

**Requirement:**
> Design should support **any openHASP device** discoverable by the HA openHASP custom integration.

**Implementation:**
```python
# Backend endpoint
GET /api/ha/devices/openhasp

# Returns all openHASP devices:
[
  {
    "entity_id": "openhasp.plate_kitchen",
    "name": "Lanbon L8 - Kitchen",
    "model": "Lanbon L8",
    "resolution": {"width": 480, "height": 320},
    "online": true
  }
]
```

### Enhanced Validation

**Validation checklist:**
1. ✅ All entity IDs exist in HA
2. ✅ No overlapping objects
3. ✅ Valid coordinates for device screen size
4. ✅ Selected openHASP device still exists in HA
5. ✅ Device is online

### Screen Size Handling

**Important:** Screen sizes are **NOT** automatically discovered by the openHASP integration.

**Our approach:**
1. Maintain device model → resolution mapping
2. Allow manual override in designer settings
3. Validate coordinates against screen size

**Common resolutions:**
- Lanbon L8: 480x320 pixels
- WT32-SC01: 320x480 pixels
- ESP32-2432S028r: 240x320 pixels

---

## Local Development & Testing Strategies

### Recommended Approach: VS Code Devcontainer

This is the **official HA development method** used by core developers.

#### What It Provides
- Full Home Assistant + Supervisor running locally
- Your add-on appears as "Local Add-on"
- Hot reload for development
- Access to HA UI at `http://localhost:7123`
- No need for separate HA instance

#### Setup Steps

**1. Prerequisites:**
```bash
# Install Docker Desktop, Rancher Desktop, or compatible Docker engine
# (Rancher Desktop: configure to use dockerd runtime)

# Install Antigravity (or VS Code)
# Install "Remote - Containers" extension
```

**2. Create devcontainer config:**

Create `.devcontainer/devcontainer.json` in your repo:
```json
{
  "name": "openHASP Designer Add-on Development",
  "image": "ghcr.io/home-assistant/devcontainer:addons",
  "appPort": ["7123:8123", "7357:4357"],
  "postStartCommand": "bash devcontainer_bootstrap",
  "extensions": [
    "ms-python.python",
    "ms-python.vscode-pylance"
  ],
  "mounts": [
    "type=volume,target=/var/lib/docker"
  ],
  "privileged": true
}
```

**3. Create bootstrap script:**

Create `devcontainer_bootstrap`:
```bash
#!/bin/bash
set -e

# Start Home Assistant Supervisor
supervisor_run &

# Wait for HA to be ready
echo "Waiting for Home Assistant to start..."
while ! curl -s http://localhost:8123 > /dev/null; do
  sleep 2
done

echo "Home Assistant is ready at http://localhost:7123"
```

**4. Open in container:**
```bash
# In Antigravity (or VS Code):
# 1. Open your repo folder
# 2. Command Palette (Cmd+Shift+P)
# 3. "Remote-Containers: Reopen in Container"
# 4. Wait for container to build (first time takes ~10 min)
```

**5. Access HA:**
```
http://localhost:7123
```

Your add-on will appear in **Settings → Add-ons → Local Add-ons**

#### Development Workflow

```bash
# Make changes to your add-on code
# In VS Code terminal:
ha addons reload openhasp_designer

# Or rebuild completely:
ha addons rebuild openhasp_designer
```

**Advantages:**
- ✅ Full HA environment
- ✅ Test integrations, services, entities
- ✅ No separate HA instance needed
- ✅ Fast iteration

**Disadvantages:**
- ⚠️ Requires Docker Desktop (resource-heavy)
- ⚠️ Initial setup time
- ⚠️ Can't test on real hardware (Lanbon L8)

---

### Alternative 1: Direct Docker Testing

For faster iteration without full HA environment.

#### Setup

**1. Comment out image in config.yaml:**
```yaml
# config.yaml
name: "openHASP Designer"
# image: "ghcr.io/..."  ← Comment this out for local build
```

**2. Build locally:**
```bash
cd your-addon-directory

# Build for your architecture
docker build -t local/openhasp-designer .

# Run with test data
docker run --rm \
  -v $(pwd)/test_data:/data \
  -p 8080:8080 \
  -e HA_URL=http://your-ha-ip:8123 \
  -e HA_TOKEN=your-token \
  local/openhasp-designer
```

**3. Test API:**
```bash
# Test backend endpoints
curl http://localhost:8080/api/status
curl http://localhost:8080/api/ha/entities
```

**Advantages:**
- ✅ Fast builds
- ✅ No full HA needed for backend testing
- ✅ Good for API development

**Disadvantages:**
- ❌ Can't test HA integration features
- ❌ No UI testing with real HA
- ❌ Manual testing only

---

### Alternative 2: Test HA Instance

Some developers run a separate test HA instance.

#### Option A: Separate Physical Device
- Raspberry Pi or old PC
- Separate network (VLAN) or same network
- Install HA OS
- Add your add-on repository

**Advantages:**
- ✅ Real hardware testing
- ✅ Isolated from production
- ✅ Can test with real openHASP devices

**Disadvantages:**
- ❌ Requires extra hardware
- ❌ Slower iteration
- ❌ Network setup complexity

#### Option B: VM on Same Machine
```bash
# Using VirtualBox or VMware
# 1. Download HA OS image
# 2. Create VM with 2GB RAM, 32GB disk
# 3. Bridge network or NAT with port forwarding
# 4. Access at VM IP
```

**Advantages:**
- ✅ No extra hardware
- ✅ Snapshots for testing
- ✅ Isolated environment

**Disadvantages:**
- ❌ Resource usage
- ❌ Can't access real hardware (Lanbon L8)

---

## Recommended Development Workflow

### Phase 1: Backend Development (Current)

**Use:** Direct Docker testing

```bash
cd backend-python

# Run backend directly (fastest)
uvicorn app.main:app --reload --port 8080

# Set environment variables
export HA_URL=http://your-production-ha:8123
export HA_TOKEN=your-token

# Test against your REAL HA instance
curl http://localhost:8080/api/ha/entities
```

**Why:** Backend is just a REST API, doesn't need full HA environment.

---

### Phase 2: Frontend Development

**Use:** Direct Docker testing + production HA

```bash
# Frontend development
cd frontend
npm run dev  # Vite dev server on :5173

# Configure to use backend
# frontend/.env
VITE_API_URL=http://localhost:8080
```

**Test flow:**
1. Frontend (localhost:5173) → Backend (localhost:8080) → Production HA

**Why:** Can develop UI without add-on packaging.

---

### Phase 3: Add-on Integration Testing

**Use:** VS Code devcontainer

```bash
# Open in devcontainer
# Add-on appears in Local Add-ons
# Install and test full integration
```

**Why:** Need to test Ingress, HA integration, device discovery.

---

### Phase 4: Production Testing

**Use:** Your production HA instance

```bash
# Push to GitHub
# GitHub Actions builds multi-arch images
# Add repo to your production HA
# Install and test with real Lanbon L8
```

**Why:** Final validation with real hardware.

---

## Short-Circuit Docker Builds

### For Local Development

**Skip multi-arch builds:**
```yaml
# .github/workflows/builder.yaml
# Comment out for local testing:
# --all \

# Use only your architecture:
--amd64 \  # or --aarch64 if on Mac M1/M2
```

**Local build without GitHub Actions:**
```bash
# Build single architecture locally
docker buildx build \
  --platform linux/amd64 \
  -t local/openhasp-designer:latest \
  .

# Test immediately
docker run --rm -p 8080:8080 local/openhasp-designer:latest
```

### For Faster Iteration

**Use Docker layer caching:**
```dockerfile
# Dockerfile - optimize layer order
FROM python:3.11-slim

# Install dependencies first (cached if requirements.txt unchanged)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code last (changes frequently)
COPY app ./app
```

**Build with cache:**
```bash
docker build --cache-from local/openhasp-designer:latest -t local/openhasp-designer:latest .
```

---

## Complete Development Setup

### Recommended Stack

```
┌─────────────────────────────────────────┐
│ Your Development Machine                │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ VS Code                             │ │
│ │ - Frontend dev (npm run dev)        │ │
│ │ - Backend dev (uvicorn --reload)    │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ Docker Desktop                      │ │
│ │ - Local builds                      │ │
│ │ - Devcontainer (when needed)        │ │
│ └─────────────────────────────────────┘ │
└────────────┬────────────────────────────┘
             │ Network
             ▼
┌─────────────────────────────────────────┐
│ Your Production HA Instance             │
│ - Real entities for testing             │
│ - Real Lanbon L8 device                 │
│ - openHASP integration installed        │
└─────────────────────────────────────────┘
```

### Environment Variables

Create `.env` files:

**Backend:**
```bash
# backend-python/.env
HA_URL=http://192.168.1.100:8123  # Your production HA
HA_TOKEN=eyJ0eXAiOiJKV1QiLCJhbGc...  # Long-lived token
HA_CONFIG_PATH=/tmp/test_config  # Local testing
```

**Frontend:**
```bash
# frontend/.env
VITE_API_URL=http://localhost:8080  # Local backend
```

---

## Summary

**For your development:**

1. **Backend API development:** Run Python directly (`uvicorn --reload`)
2. **Frontend development:** Run Vite dev server (`npm run dev`)
3. **Integration testing:** VS Code devcontainer (when needed)
4. **Final testing:** Production HA + GitHub Actions builds

**No need for:**
- ❌ Separate test HA instance (use devcontainer instead)
- ❌ VLAN setup (develop against production HA is fine)
- ❌ Complex Docker builds during development (use direct execution)

**Short-circuit builds:**
- Use `--reload` for backend (no Docker)
- Use Vite HMR for frontend (no Docker)
- Only build Docker for integration testing
- Let GitHub Actions handle multi-arch production builds
