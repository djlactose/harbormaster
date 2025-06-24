# HarborMaster

**HarborMaster** is a lightweight web dashboard that provides a clean, responsive homepage for managing your running Docker containers. It automatically detects container ports, shows thumbnails of web UIs, and lets you customize access points.

---

## 🚢 Features

- ⚓ Auto-discovers running Docker containers
- 🌐 Clickable links for HTTP/HTTPS web ports
- 🖼️ Automatic UI screenshots for web-enabled containers
- 🔄 Auto-refresh with customizable intervals
- 🎛️ Toggle to show stopped or unmapped containers
- 🌙 Light/Dark mode with theme toggle
- ✏️ Inline per-container IP overrides
- 🔍 Search and filter containers by name
- 📊 Sort containers by name, status, image, or number of ports
- 📁 No external database — configuration is saved to a local JSON file

---

## 🧱 Requirements

- Python 3.8+
- Docker daemon (socket access)
- Headless Chromium support (via `pyppeteer`)

### Python dependencies

See `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/djlactose/harbormaster.git
cd harbormaster
```

### 2. Build and run with Docker

```bash
docker build -t harbormaster .
docker run -d -p 8080:8080 -v /var/run/docker.sock:/var/run/docker.sock --name harbormaster harbormaster
```

You can also persist settings by mounting a volume:

```bash
docker run -d -p 8080:8080 -v /var/run/docker.sock:/var/run/docker.sock -v $(pwd)/data:/data --name harbormaster harbormaster
```

---

## ⚙️ Configuration

Settings are stored in `/data/settings.json` and include:

```json
{
  "base_ip": "192.168.1.100",
  "overrides": {
    "nginx-container": "192.168.1.101"
  },
  "show_stopped": true,
  "show_unmapped": false,
  "auto_refresh_seconds": 10,
  "sort_by": "name"
}
```

All settings can now be controlled directly from the web UI.

---

## 🧪 Screenshot Generation

Screenshots of web-enabled containers are automatically generated using `pyppeteer`. They are saved in:

```
/static/thumbnails/
```

You can manually trigger this by visiting the dashboard, or call:

```bash
python screenshot.py <container_port_name> <url>
```

---

## 🎨 Theming & Icons

- Logos and icons are served from `/static/icons/`
- You can override container icons by name
- Dark and light mode logos are supported

---

## 🛟 Credits

Created by [djlactose](https://github.com/djlactose).  
Modified and maintained for UI improvements, sorting, AJAX refresh, and theming.

---

## 📜 License

MIT License. Use freely and contribute if you'd like!