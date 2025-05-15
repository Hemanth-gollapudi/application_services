FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure Python can find sources in src
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

# Switch to source directory as default workdir for runtime
WORKDIR /app/src

EXPOSE 8000

CMD ["uvicorn", "tenant_user_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
