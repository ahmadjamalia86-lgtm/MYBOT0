FROM python:3.11-slim

WORKDIR /app

# تثبيت ffmpeg المطلوب لـ yt-dlp
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملف المتطلبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ ملف البوت
COPY main.py .

# إنشاء مجلد مؤقت
RUN mkdir -p /tmp/bot_downloads

# تشغيل البوت
CMD ["python", "main.py"]