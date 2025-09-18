# Use NVIDIA CUDA base image with PyTorch
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip ffmpeg git curl && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy your Streamlit app code into container
COPY . .

# Streamlit runs on port 8080 (Cloud Run requirement)
ENV PORT=8080

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.headless=true"]
