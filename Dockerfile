FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libssl-dev \
    zip \
    && rm -rf /var/lib/apt/lists/*

RUN wget -O /tmp/zsign.zip https://github.com/zhlynn/zsign/archive/refs/heads/master.zip \
    && unzip /tmp/zsign.zip -d /tmp/ \
    && cd /tmp/zsign-master \
    && g++ *.cpp -o zsign -lcrypto \
    && cp zsign /usr/local/bin/ \
    && rm -rf /tmp/zsign*

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]
