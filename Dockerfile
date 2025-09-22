FROM gcr.io/deeplearning-platform-release/pytorch-gpu.2-1

WORKDIR /app

# Install extra system packages
RUN apt-get update && apt-get install -y ffmpeg git wget unzip && rm -rf /var/lib/apt/lists/*

# Clone RVC WebUI repo (contains tools/infer_cli.py)
RUN git clone https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git rvcwebui

# Download pretrained Hubert model
RUN wget https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt -O /app/rvcwebui/assets/hubert/hubert_base.pt

# Copy your requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app
COPY . .

# Expose Cloud Run port
EXPOSE 8080

# Run Streamlit
ENTRYPOINT ["streamlit", "run", "colab_accent_converter.py"]
CMD ["--server.port=8080", "--server.address=0.0.0.0"]