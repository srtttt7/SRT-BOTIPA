FROM alpine:3.18

RUN apk add --no-cache \
    python3 \
    py3-pip \
    git \
    g++ \
    make \
    cmake \
    openssl-dev \
    zip \
    unzip

RUN git clone --recursive https://github.com/zhlynn/zsign.git /tmp/zsign \
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
