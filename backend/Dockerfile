FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY source_code/ ./source_code/

# Create directories for model storage
RUN mkdir -p /app/models /app/output_data /app/sample_evidence

# Expose API port
EXPOSE 8001

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run the API
CMD ["uvicorn", "source_code.api.app:app", "--host", "0.0.0.0", "--port", "8001"]

