FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    libssl-dev \
    zip \
    unzip \
    && git clone https://github.com/zhly2013/zsign.git \
    && cd zsign \
    && g++ *.cpp common/*.cpp -lcrypto -O3 -o zsign \
    && mv zsign /usr/local/bin/ \
    && chmod +x /usr/local/bin/zsign \
    && cd .. && rm -rf zsign \
    && apt-get clean

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
