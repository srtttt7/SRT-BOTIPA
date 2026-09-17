FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    git \
    g++ \
    make \
    cmake \
    libssl-dev \
    zip \
    unzip \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --recursive https://github.com/zhlynn/zsign.git /tmp/zsign \
    && cd /tmp/zsign \
    && mkdir build && cd build \
    && cmake -DCMAKE_BUILD_TYPE=Release .. \
    && make \
    && cp zsign /usr/local/bin/ \
    && chmod +x /usr/local/bin/zsign \
    && rm -rf /tmp/zsign

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]
