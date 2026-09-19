FROM nikolaik/python-nodejs:python3.10-nodejs20-slim

# 1. System dependencies install karein
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg git python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 2. Working directory
WORKDIR /app

# 3. Code copy karein
COPY . .

# 4. Requirements install karein
RUN pip3 install --no-cache-dir -U -r requirements.txt

# 5. NODE JS VERIFY KAREIN (Ye step check karega ki node hai ya nahi)
RUN node -v && npm -v

# 6. Bot start karein (direct launch, no interactive installer)
COPY docker-start /app/docker-start
RUN chmod +x /app/docker-start
CMD ["bash", "docker-start"]
