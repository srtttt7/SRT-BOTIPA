FROM python:3.10-slim

# 1. تثبيت الحزم والأدوات اللازمة لتجميع أداة zsign
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    libssl-dev \
    zip \
    && rm -rf /var/lib/apt/lists/*

# 2. تحميل وتجميع أداة zsign بنجاح
RUN git clone https://github.com/zhly201/zsign.git /tmp/zsign \
    && cd /tmp/zsign \
    && g++ *.cpp common/*.cpp -lcrypto -O3 -o /usr/local/bin/zsign \
    && rm -rf /tmp/zsign

# 3. إعداد المجلد الرئيسي وتنسيق العمل
WORKDIR /app

# 4. نسخ التبعيات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. نسخ باقي ملفات البوت
COPY . .

# 6. تشغيل ملف البوت الرئيسي
CMD ["python", "bot.py"]
