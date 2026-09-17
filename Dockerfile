FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    wget \
    libssl-dev \
    zip \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN wget -O /usr/local/bin/zsign https://github.com/zhlynn/zsign/raw/master/zsign || \
    (wget -O /tmp/zsign.tar.gz https://github.com/sachin9/zsign-static/releases/download/v1.0.0/zsign && mv /tmp/zsign /usr/local/bin/zsign) \
    && chmod +x /usr/local/bin/zsign

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]
