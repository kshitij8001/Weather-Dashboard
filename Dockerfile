# ==============================================================================
# Dockerfile for Weather Dashboard (Flask Web Application)
# Course: TYCSE Cloud Computing & DevOps - CCA 2
# ==============================================================================

FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    APP_VERSION=1.0.0 \
    ENVIRONMENT=production

WORKDIR /app

# Install security and runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies first (leveraging Docker layer caching)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app.py /app/
COPY weather_service.py /app/
COPY templates /app/templates
COPY static /app/static

# Create non-root user for security best practices
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose standard application port
EXPOSE 5000

# Container Healthcheck (verifies /health endpoint)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Production WSGI server using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "2", "--timeout", "60", "app:app"]
