FROM python:3.10-slim

# تثبيت الأدوات الأساسية لبناء zsign
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    cmake \
    libssl-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# تنزيل وبناء أداة zsign مع تفادي مشاكل المصادقة
RUN git config --global advice.detachedHead false && \
    git clone --depth 1 https://github.com/zhlynn/zsign.git /zsign && \
    cd /zsign && \
    g++ *.cpp common/*.cpp -lcrypto -ldl -O3 -o /usr/local/bin/zsign && \
    rm -rf /zsign

WORKDIR /app

# نسخ وتثبيت متطلبات البوت
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
