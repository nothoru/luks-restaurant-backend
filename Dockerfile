# Stage 1: Build the virtual environment with all dependencies
FROM python:3.11 as builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


# Stage 2: Create the final, slim production image
FROM python:3.11-slim

WORKDIR /app

RUN addgroup --system app && adduser --system --group app

COPY --from=builder /opt/venv /opt/venv

# Explicitly copy the project files with correct ownership
COPY --chown=app:app . .

ENV PATH="/opt/venv/bin:$PATH"

# This chown is now redundant but harmless, we can leave it
RUN chown -R app:app /app

USER app

EXPOSE 8000

CMD ["gunicorn", "--chdir", "/app", "-w", "4", "backend.wsgi:application"]