# Base image
FROM python:3.11-slim

# Ishchi katalog
WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bot kodi
COPY . .

# Environment variable orqali credentials yo‘lini olamiz
ENV GOOGLE_APPLICATION_CREDENTIALS="/secrets/credentials.json"

# Telegram botni ishga tushirish
CMD ["python", "main.py"]
