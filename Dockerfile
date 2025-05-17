FROM python:3.10

WORKDIR /app

# Install git
RUN apt-get update && apt-get install -y git

# Clone the goaldsl repository
RUN git clone https://github.com/robotics-4-all/goal-dsl/

# Change directory, checkout the specific tag, and install
WORKDIR /app/goal-dsl
RUN git checkout v0.2.0
RUN pip install .

# Return to your app directory
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
