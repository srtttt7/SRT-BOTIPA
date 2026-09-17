FROM python:3.10-slim

# تثبيت التبعيات الأساسية
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    libssl-dev \
    zip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# تنزيل zsign وتجميعه بشكل منفصل مع تفادي مشاكل الشبكة
RUN git clone --depth 1 https://github.com/zhly201/zsign.git /tmp/zsign
WORKDIR /tmp/zsign
RUN g++ *.cpp common/*.cpp -lcrypto -O3 -o /usr/local/bin/zsign
RUN rm -rf /tmp/zsign

# إعداد بيئة العمل
WORKDIR /app

# نسخ التبعيات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ ملفات المشروع
COPY . .

# تشغيل البوت
CMD ["python", "bot.py"]
