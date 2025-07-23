# Stage 1: Build the virtual environment with all dependencies
FROM python:3.11 as builder

# Install system dependencies required by packages like OpenCV, Pillow, and psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Create and activate a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install python packages
RUN pip install --upgrade pip
# The --no-cache flag is added here to reduce memory usage during build
RUN pip install --no-cache-dir --no-cache -r requirements.txt