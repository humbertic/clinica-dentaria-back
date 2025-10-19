FROM python:3.13-slim

# Install system dependencies for WeasyPrint
RUN apt-get update && apt-get install -y \
    libgobject-2.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libfontconfig1 \
    libgdk-pixbuf2.0-0 \
    libxml2 \
    libxslt1.1 \
    libffi7 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Start server without migrations for now
CMD uvicorn src.main:app --host 0.0.0.0 --port $PORT