# HarborMaster

**HarborMaster** is a lightweight web dashboard for your Docker ecosystem. It displays running containers and Swarm services with clickable web links, auto-refresh, thumbnail previews, and intuitive sorting/filtering — all without any database.

---

## ⚓ Features

- ✅ Unified view of:
  - Docker containers
  - Docker Swarm services
- 🔍 Container and service discovery via Docker socket
- 🌐 Clickable web links for HTTP/HTTPS ports
- 🧭 Supports TCP **and** UDP port visibility
- 🖼️ Live thumbnail previews of web UIs
- ✏️ Per-container IP overrides (for reverse proxies or remote hosts)
- 🌓 Light & dark mode with theme toggle
- 🔄 Auto-refresh with configurable intervals
- 🧰 Sort by name, image, port count, or status
- 🧪 All settings saved locally as JSON — no database needed

---

## 🐳 Docker Image

You can pull and run the official image from Docker Hub:

```bash
docker pull djlactose/harbormaster
```

🔗 [Docker Hub Repository](https://hub.docker.com/r/djlactose/harbormaster)

---

## 🚀 Getting Started

### 1. Clone and Build

```bash
git clone https://github.com/djlactose/harbormaster.git
cd harbormaster
docker build -t harbormaster .
```

### 2. Run It (Bind Docker Socket)

```bash
docker run -d -p 8080:8080 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd)/data:/data \
  --name harbormaster \
  harbormaster
```

> Mounting `/data` allows settings to persist across restarts.

---

## ⚙️ Configuration

All settings are stored in a JSON file:

```json
/data/settings.json
```

Example contents:

```json
{
  "base_ip": "192.168.1.10",
  "overrides": {
    "nginx": "192.168.1.12"
  },
  "show_stopped": true,
  "show_unmapped": false,
  "auto_refresh_seconds": 10,
  "sort_by": "name"
}
```

These can also be changed from the dashboard UI.

---

## 🐝 Swarm Support

- Swarm services are shown with a Swarm icon.
- Published ports (TCP/UDP) are detected and displayed.
- Underlying task containers are **excluded** to avoid duplication.
- Clickable links are generated if a service responds to HTTP or HTTPS.

To deploy HarborMaster to all nodes in a Swarm:

```bash
docker service create --mode global \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -p 8080:8080 \
  --name harbormaster \
  djlactose/harbormaster
```

---

## 📸 Screenshot Thumbnails

HarborMaster attempts to take live screenshots of container web UIs.

- Saved in `/static/thumbnails/`
- Uses `pyppeteer` under the hood
- Only attempts capture if HTTP/HTTPS is detected

You can trigger a screenshot manually:

```bash
python screenshot.py <name_port> <url>
```

---

## 🎨 Customization

- `static/icons/` contains:
  - `generic.png` for unknown services
  - `swarm.png` for Docker Swarm services
  - `logo_light.png` / `logo_dark.png` for branding

You can add custom icons by service name or image match.

---

## 🧪 Development

Dependencies:

```bash
pip install -r requirements.txt
```

Then run locally:

```bash
python app.py
```

Access at: `http://localhost:8080`

---

## 📜 License

MIT License  
Copyright © djlactose

---

## 🙌 Credits

Built on the Docker SDK for Python.  
Enhanced UI + Swarm support by community contributors.
