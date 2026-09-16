# ==============================================================================
# VeriNews AI - Production Docker Container Specification
# ==============================================================================
FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable unbuffered logging with minimal memory footprint
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    TOKENIZERS_PARALLELISM=false \
    PORT=8000

WORKDIR /app

# Install system utilities & SSL certificates
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY requirements.txt .

# Install lightweight PyTorch CPU wheels followed by application requirements
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy application backend and frontend files
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

# Set working directory to backend
WORKDIR /app/backend

# Expose backend port
EXPOSE 8000

# Health check instruction for cloud load balancers & orchestrators
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Launch production server via Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
