# Use official Python image as a parent image
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Expose WebSocket port
EXPOSE 8765

# Run the WebSocket server
CMD ["python", "main.py"]
