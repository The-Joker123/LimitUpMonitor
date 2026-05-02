# ---- Stage 1: Build frontend ----
FROM node:20-slim AS frontend-builder
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci || npm install
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python runtime ----
FROM python:3.11-slim
WORKDIR /app

# System deps for pandas/numpy compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps (cached layer)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ .

# Copy built frontend
COPY --from=frontend-builder /build/dist /frontend/dist

# Default config
COPY config.json.example /config.json
RUN mkdir -p /data && cp /config.json /data/config.json

ENV CONFIG_FILE=/data/config.json
ENV ALLOWED_ORIGINS=*
ENV PORT=7860

EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
