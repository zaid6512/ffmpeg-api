# Use official Python runtime as base image
FROM python:3.10-slim

# Install FFmpeg and clean up cache
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Set working directory
WORKDIR /app

# Copy all project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the Render port
ENV PORT=10000
EXPOSE 10000

# Start the app
CMD gunicorn server:app --bind 0.0.0.0:$PORT
