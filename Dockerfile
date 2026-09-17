FROM python:3.10-slim

# تثبيت الحزم المطلوبة
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    cmake \
    libssl-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# تنزيل وبناء zsign باستخدام cmake
RUN git clone https://github.com/zhlynn/zsign.git /zsign-src && \
    mkdir -p /zsign-src/build && \
    cd /zsign-src/build && \
    cmake .. && \
    make -j$(nproc) && \
    cp zsign /usr/local/bin/ && \
    rm -rf /zsign-src

WORKDIR /app

# تثبيت متطلبات البوت
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
