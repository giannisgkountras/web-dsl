FROM python:3.10

WORKDIR /app

# Install git
RUN apt-get update && apt-get install -y apache2-utils

# Return to your app directory
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
