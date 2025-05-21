FROM python:3.10-slim

# Add build argument for version
ARG BUILD_VERSION
LABEL version=${BUILD_VERSION}

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY services/tenant_user-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the service code
COPY services/tenant_user-service /app/
COPY services/tenant_user-service/src /app/src/

# Create a non-root user and switch to it
RUN useradd -m appuser && \
    chown -R appuser:appuser /app
USER appuser

# Ensure Python can find sources in src
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

# Switch to source directory as default workdir for runtime
WORKDIR /app/src

EXPOSE 8000

CMD ["uvicorn", "tenant_user_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
