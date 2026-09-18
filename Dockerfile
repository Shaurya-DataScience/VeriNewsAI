# ==============================================================================
# VeriNews AI - Production Docker Container Specification
# Optimized for Hugging Face Spaces (2 vCPUs, 16GB RAM) & Cloud Containers
# ==============================================================================
FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    TOKENIZERS_PARALLELISM=false \
    PORT=8000

# Install system utilities & build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set up dedicated non-root user (UID 1000 required by Hugging Face Spaces)
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    TORCH_HOME=/home/user/.cache/torch \
    HF_HOME=/home/user/.cache/huggingface

WORKDIR /app

# Copy dependency specifications
COPY requirements.txt .

# Install lightweight PyTorch CPU wheels followed by application requirements
RUN pip install --no-cache-dir torch --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy application backend and frontend files
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

# Ensure appropriate directory permissions for user 1000
RUN mkdir -p /app/backend/data /home/user/.cache && \
    chown -R user:user /app /home/user

# Switch to non-root user
USER user

# Set working directory to backend
WORKDIR /app/backend

# Expose backend port
EXPOSE 8000

# Health check instruction
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Launch production server via Uvicorn with dynamic port binding
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
