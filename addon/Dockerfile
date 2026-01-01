# ============================================================================
# Stage 1: Frontend Build
# ============================================================================
FROM node:18-alpine AS frontend-builder

WORKDIR /build

# Copy package files
COPY frontend/package*.json ./

# Install dependencies (use install instead of ci for flexibility)
RUN npm install

# Copy frontend source
COPY frontend/ ./

# Build for production
RUN npm run build

# ============================================================================
# Stage 2: Backend Dependencies
# ============================================================================
FROM python:3.11-alpine AS backend-builder

WORKDIR /build

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev

# Copy requirements
COPY backend-python/requirements.txt ./

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 3: Final Image
# ============================================================================
FROM ghcr.io/home-assistant/amd64-base:latest

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install runtime dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    bash

# Create app directory
WORKDIR /app

# Copy frontend build
COPY --from=frontend-builder /build/dist /app/frontend/dist

# Copy backend
COPY backend-python /app/backend

# Copy Python dependencies from builder
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy add-on files
COPY addon/run.sh /
RUN chmod a+x /run.sh

# Labels
LABEL \
    io.hass.name="openHASP Designer" \
    io.hass.description="Visual designer for openHASP with Home Assistant integration" \
    io.hass.type="addon" \
    io.hass.version="1.0.0"

# Expose ports
EXPOSE 5173 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/api/health || exit 1

# Start
CMD ["/run.sh"]
