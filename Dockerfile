FROM python:3.11-slim

# Install dependencies for Chromium
RUN apt-get update && apt-get install -y \
    wget gnupg ca-certificates \
    fonts-liberation libnss3 libatk-bridge2.0-0 libxss1 libgtk-3-0 \
    libasound2 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
    libxshmfence1 libxext6 libegl1 libx11-6 libxfixes3 \
    --no-install-recommends && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

VOLUME data

RUN mkdir -p static/thumbnails

# Install Python dependencies
RUN pip install --no-cache-dir flask docker pyppeteer requests

# Download Chromium (no async needed)
RUN python -c "from pyppeteer import chromium_downloader; chromium_downloader.download_chromium()"

EXPOSE 8080
CMD ["python", "app.py"]
