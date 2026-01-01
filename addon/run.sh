#!/usr/bin/with-contenv bashio

# Check if running in Home Assistant add-on mode
if command -v bashio::config &> /dev/null; then
    # Running as HA add-on
    HA_URL=$(bashio::config 'ha_url' || echo "${HA_URL:-http://supervisor/core}")
    HA_TOKEN=$(bashio::config 'ha_token' || echo "${HA_TOKEN}")
    
    # If token is empty, try to use Supervisor token
    if [ -z "$HA_TOKEN" ]; then
        bashio::log.info "No token provided, using Supervisor token"
        HA_TOKEN="${SUPERVISOR_TOKEN:-}"
    fi
else
    # Running standalone (for testing)
    echo "[INFO] Running in standalone mode"
    HA_URL="${HA_URL:-http://homeassistant.local:8123}"
    HA_TOKEN="${HA_TOKEN:-}"
fi

# Set environment variables for backend
export HA_URL="${HA_URL}"
export HA_TOKEN="${HA_TOKEN}"
export HA_CONFIG_PATH="/config/openhasp"

# Create config directory if it doesn't exist
mkdir -p /config/openhasp

# Log function that works in both modes
log_info() {
    if command -v bashio::log.info &> /dev/null; then
        bashio::log.info "$1"
    else
        echo "[INFO] $1"
    fi
}

log_info "Starting openHASP Designer..."
log_info "Home Assistant URL: ${HA_URL}"
log_info "Config path: ${HA_CONFIG_PATH}"

# Start backend API
log_info "Starting backend API on port 8080..."
cd /app/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080 &
BACKEND_PID=$!

# Wait for backend to be ready
sleep 3

# Start frontend (served via Ingress on port 5173)
log_info "Starting frontend on port 5173..."
cd /app/frontend/dist
python3 -m http.server 5173 &
FRONTEND_PID=$!

log_info "openHASP Designer started successfully"
log_info "Access via Home Assistant Ingress panel or http://localhost:5173"

# Function to handle shutdown
shutdown() {
    log_info "Shutting down openHASP Designer..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

# Trap signals
trap shutdown SIGTERM SIGINT

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
