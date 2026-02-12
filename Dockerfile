# استخدام صورة Python الرسمية
FROM python:3.11-slim

# تعيين مجلد العمل
WORKDIR /app

# نسخ ملفات المتطلبات
COPY requirements.txt .

# تثبيت المتطلبات
RUN pip install --no-cache-dir -r requirements.txt

# نسخ ملفات البوت
COPY bot.py .

# تعيين متغيرات البيئة
ENV PYTHONUNBUFFERED=1

# تشغيل البوت
CMD ["python", "bot.py"]
