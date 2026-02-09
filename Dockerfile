FROM python:3.10-slim

# تحديث النظام وتثبيت FFmpeg الضروري لدمج الصوت والصورة
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# تثبيت مكتبات بايثون
RUN pip install --no-cache-dir -r requirements.txt

# تشغيل البوت
CMD ["python", "main.py"]
