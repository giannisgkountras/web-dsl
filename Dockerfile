FROM python:3.10

WORKDIR /app

# Install system dependencies (including npm)
RUN apt-get update && apt-get install -y \
    npm \
    && rm -rf /var/lib/apt/lists/*
    
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
