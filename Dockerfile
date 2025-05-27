FROM python:3.10

WORKDIR /app

RUN apt-get update && apt-get install -y \
    apache2-utils \
    openssh-client \
    sshpass

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python", "-u", "/app/entrypoint.py"]
