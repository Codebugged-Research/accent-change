# Use NVIDIA CUDA base image with Python
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

# Install Python + tools
RUN apt-get update && apt-get install -y \
    python3 python3-pip ffmpeg git wget && \
    rm -rf /var/lib/apt/lists/*

# Set Python3 as default
RUN ln -s /usr/bin/python3 /usr/bin/python

# Set working directory
WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt


COPY . .

EXPOSE 8080

CMD ["streamlit", "run", "colab_accent_converter.py", "--server.port=$PORT", "--server.address=0.0.0.0"]
