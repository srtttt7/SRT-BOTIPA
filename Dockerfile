FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    g++ \
    make \
    cmake \
    libssl-dev \
    zip \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/zhlynn/zsign.git /tmp/zsign \
    && cd /tmp/zsign \
    && mkdir build && cd build \
    && cmake .. \
    && make \
    && cp zsign /usr/local/bin/ \
    && rm -rf /tmp/zsign

WORKDIR /app
COPY . /app

RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["python3", "bot.py"]
