# Python 3.11 image-dan boshlaymiz
FROM python:3.11-slim

# Ishchi direktoriyani o‘rnatamiz
WORKDIR /app

# Talab qilinadigan paketlarni o‘rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Loyihani konteynerga nusxalash
COPY . .

# Telegram botni ishga tushirish
CMD ["python", "main.py"]
