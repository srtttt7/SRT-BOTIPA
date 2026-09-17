FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    git \
    zip \
    unzip \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir isign

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]
