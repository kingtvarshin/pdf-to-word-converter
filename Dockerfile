FROM python:3.10-slim

# Install system dependencies and all tesseract language packs
RUN apt-get update && \
    apt-get install -y tesseract-ocr-all poppler-utils && \
    rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY flask-pdf-to-word-app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY flask-pdf-to-word-app/src/ .

# Expose Flask port
EXPOSE 5123

# Run the app
CMD ["python", "app.py"]