# ========================================================
# ClipForge AI Video Editor — Dockerfile
# ========================================================
FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies: FFmpeg, libass, fonts, and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libfontconfig1 \
    fonts-liberation \
    fonts-dejavu-core \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and assets
COPY . .

# Create necessary directories
RUN mkdir -p "Raw Footage" Export engine/temp assets/sfx assets/cache/logos

EXPOSE 5050

# Run FastAPI Web Studio
CMD ["python", "-m", "uvicorn", "engine.server:app", "--host", "0.0.0.0", "--port", "5050"]
