FROM python:3.11-slim

# Copy project files
COPY static/ /app/static/
COPY templates/ /app/templates/
COPY app.py /app/app.py 
COPY screenshot.py /app/screenshot.py
COPY settings.json /data/settings.json
COPY requirements.txt /app/requirements.txt
COPY LICENSE /app/LICENSE

# Expose the app port
EXPOSE 8080

# Set work directory
WORKDIR /app

# Install required system packages for pyppeteer / Chromium
RUN apt-get update && \ 
apt-get install -y wget gnupg ca-certificates fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 libatk1.0-0 libcups2 libdbus-1-3 libgdk-pixbuf2.0-0 libnspr4 libnss3 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 xdg-utils libu2f-udev libvulkan1 libxcb1 libxss1 && \
apt-get clean && rm -rf /var/lib/apt/lists/* && \
pip install --no-cache-dir -r requirements.txt && \
python3 -c "import asyncio; from pyppeteer import launch; asyncio.get_event_loop().run_until_complete(launch(headless=True, args=['--no-sandbox']))" && \
mkdir -p /app/static/thumbnails

# Run the Flask app
CMD ["python", "app.py"]