# Base image
FROM python:3.11-slim

# Working directory
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    libfreetype6-dev \
    libpng-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (Telegram bot polling does not need HTTP port)
# ENV variables from .env will be used automatically by python-dotenv

# Command to run the bot
CMD ["python", "main.py"]
