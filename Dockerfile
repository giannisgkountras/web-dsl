FROM python:3.10

WORKDIR /
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "web_dsl.api:api", "--host", "0.0.0.0", "--port", "8000"]%
