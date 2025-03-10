FROM python:3.10

WORKDIR /

# Install system dependencies (including npm)
RUN apt-get update && apt-get install -y \
    npm \
    && rm -rf /var/lib/apt/lists/*
    
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "web_dsl.api:api", "--host", "0.0.0.0", "--port", "8000"]%
