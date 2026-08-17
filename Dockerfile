FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt /app/backend/
WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
WORKDIR /app
COPY backend /app/backend
COPY frontend /app/frontend

# Set working directory to backend where main.py resides
WORKDIR /app/backend

# Expose port 8000
EXPOSE 8000

# Create uploads directory
RUN mkdir -p uploads

# Start FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
