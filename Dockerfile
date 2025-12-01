# Use official Python runtime as a parent image
# Using 3.10 to ensure compatibility and avoid EOL warnings
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for OpenCV and other libs
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port Streamlit runs on
EXPOSE 8080

# Command to run the application
# Cloud Run expects the app to listen on PORT environment variable (default 8080)
CMD streamlit run app.py --server.port 8080 --server.address 0.0.0.0
