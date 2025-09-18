# Use Google prebuilt GPU PyTorch image
FROM gcr.io/deeplearning-platform-release/pytorch-gpu.2-1

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Expose Cloud Run port
EXPOSE 8080

# Start Streamlit
ENTRYPOINT ["streamlit", "run", "colab_accent_converter.py"]
CMD ["--server.port=8080", "--server.address=0.0.0.0"]
