# Dockerfile for Kafka Producer
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy application files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# Run the producer script
CMD ["python", "producer.py"]
