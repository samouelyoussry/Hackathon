# Use official Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Install pip and Streamlit separately to ensure it's available in PATH
RUN pip install --upgrade pip && pip install streamlit

# Copy project files
COPY . /app/

# Install project dependencies
RUN pip install -r requirements.txt

# Expose Streamlit default port
EXPOSE 8501

# Run the Streamlit app using Python -m to ensure it's found
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
