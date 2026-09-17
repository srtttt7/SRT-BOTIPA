FROM qingcong3/zsign:latest

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    zip \
    unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["python3", "bot.py"]
