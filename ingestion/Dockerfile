# Dockerfile for ingestion service
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

CMD ["python", "main.py"]
