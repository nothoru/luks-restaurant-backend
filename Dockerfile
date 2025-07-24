# luks-restaurant-backend/Dockerfile

# 1. Use an official Python runtime as a parent image
FROM python:3.12-slim

# 2. Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Set the working directory in the container
WORKDIR /app

# 4. Install dependencies
# Copy only the requirements file to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the application's code
COPY . .

# 6. Expose the port Gunicorn will run on
EXPOSE 8000

# 7. Run the application
# collectstatic will be run by a startup script in Azure
# For now, this is the command to start the server.
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000"]