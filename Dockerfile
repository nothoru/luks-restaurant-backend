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
RUN pip install --no-cache-dir -r requirements.txt


# Stage 2: Create the final, slim production image
FROM python:3.11-slim

WORKDIR /app

# Create a non-root user for security
RUN addgroup --system app && adduser --system --group app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the application code
COPY . .

# Set the PATH to include the venv
ENV PATH="/opt/venv/bin:$PATH"

# Change ownership of the app directory to the non-root user
RUN chown -R app:app /app

# Switch to the non-root user
USER app

EXPOSE 8000

# The command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend.wsgi"]