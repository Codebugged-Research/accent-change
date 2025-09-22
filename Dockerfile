# Use Google prebuilt GPU PyTorch image
FROM gcr.io/deeplearning-platform-release/pytorch-gpu.2-1

WORKDIR /app

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app
COPY . .

# Expose Cloud Run port
EXPOSE 8080

# Run Streamlit
ENTRYPOINT ["streamlit", "run", "colab_accent_converter.py"]
CMD ["--server.port=8080", "--server.address=0.0.0.0"]
