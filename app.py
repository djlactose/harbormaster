from flask import Flask, render_template_string, request, redirect, send_file
import docker, json, os, socket, subprocess, requests, platform, io, asyncio

app = Flask(__name__)
client = docker.DockerClient(base_url='unix://var/run/docker.sock')
SETTINGS_FILE = '/data/settings.json'

DASHBOARD_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta http-equiv="refresh" content="{{ refresh }}">
  <title>HarborMaster Dashboard</title>
  <style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #eef3f7; padding: 30px; color: #222; }
    h1 { color: #2c3e50; }
    a { color: #2980b9; text-decoration: none; }
    a:hover { text-decoration: underline; }
    input[type=text], input[type=number] {
      padding: 6px; width: 300px; margin: 5px 0; border: 1px solid #ccc; border-radius: 4px;
    }
    .container-card {
      background: #fff; padding: 20px; margin: 20px 0; border-radius: 10px;
      box-shadow: 0 4px 10px rgba(0,0,0,0.05); display: flex; align-items: center;
    }
    .container-card img.icon { height: 36px; width: 36px; margin-right: 15px; }
    .thumbnail { height: 100px; margin-left: auto; border: 1px solid #ccc; border-radius: 6px; }
    .ports a { display: inline-block; background: #dff0d8; color: #3c763d; padding: 4px 8px; border-radius: 4px; margin: 2px 0; text-decoration: none; font-size: 0.9em; }
    .ports a:hover { background: #c8e5bc; }
    .ports span { display: inline-block; background: #f5f5f5; padding: 4px 8px; border-radius: 4px; font-size: 0.9em; margin: 2px 0; }
    .section-title { margin-top: 40px; font-size: 1.5em; border-bottom: 2px solid #ccc; padding-bottom: 5px; color: #34495e; }
  </style>
  <script>
    function filterContainers() {
      let query = document.getElementById('filterInput').value.toLowerCase();
      document.querySelectorAll('.container-card').forEach(card => {
        const name = card.querySelector('strong').innerText.toLowerCase();
        card.style.display = name.includes(query) ? '' : 'none';
      });
    }
  </script>
</head>
<body>
  <h1>🛥️ HarborMaster Dashboard</h1>
  <a href="/settings">⚙️ Settings</a><br><br>
  <input type="text" id="filterInput" onkeyup="filterContainers()" placeholder="🔍 Filter containers...">

  <div class="section-title">Web Containers</div>
  {% for c in containers %}
    <div class="container-card">
      <img src="{{ c.icon }}" class="icon">
      <div>
        <strong>{{ c.name }}</strong>
        <div class="ports">
          {% for p, scheme in c.ports %}
            <a href="{{ scheme }}://{{ c.ip }}:{{ p }}" target="_blank">{{ scheme }}://{{ c.ip }}:{{ p }}</a><br>
          {% endfor %}
        </div>
      </div>
      <img class="thumbnail" src="/thumbnail/{{ c.name }}_{{ c.ports[0][0] }}">
    </div>
  {% endfor %}

  <div class="section-title">Other Containers</div>
  {% for c in others %}
    <div class="container-card">
      <img src="{{ c.icon }}" class="icon">
      <div>
        <strong>{{ c.name }}</strong>
        <div class="ports">
          {% for p in c.ports %}
            <span>{{ c.ip }}:{{ p }}</span><br>
          {% endfor %}
        </div>
      </div>
    </div>
  {% endfor %}
</body>
</html>
"""

SETTINGS_TEMPLATE = """
<!doctype html>
<html>
<head><title>HarborMaster Settings</title></head>
<body>
  <h1>⚙️ Settings</h1>
  <form method="post">
    Base IP: <input type="text" name="base_ip" value="{{ settings.base_ip }}"><br>
    Auto Refresh (seconds): <input type="number" name="auto_refresh_seconds" value="{{ settings.auto_refresh_seconds }}"><br>
    <input type="checkbox" name="show_stopped" {% if settings.show_stopped %}checked{% endif %}> Show stopped containers<br>
    <input type="checkbox" name="show_unmapped" {% if settings.show_unmapped %}checked{% endif %}> Show containers without mapped ports<br>
    <h2>Container IP Overrides</h2>
    {% for name, ip in settings.overrides.items() %}
      {{ name }}: <input type="hidden" name="container_name" value="{{ name }}">
      <input type="text" name="container_ip" value="{{ ip }}"><br>
    {% endfor %}
    <br>New container override:<br>
    Name: <input type="text" name="container_name"> IP: <input type="text" name="container_ip"><br>
    <input type="submit" value="Save">
  </form>
  <br>
  <a href="/">⬅️ Back to Dashboard</a>
</body>
</html>
"""

def generate_screenshot(name, url, path):
    try:
        subprocess.run(["python", "screenshot.py", name, url], timeout=15)
        return os.path.exists(path)
    except Exception as e:
        print(f"[ERROR] Subprocess screenshot failed: {e}")
        return False

def load_settings():
    default_settings = {
        "base_ip": "",
        "auto_refresh_seconds": 10,
        "show_stopped": False,
        "show_unmapped": False,
        "overrides": {}
    }
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            try:
                settings = json.load(f)
            except json.JSONDecodeError:
                settings = default_settings.copy()
    else:
        settings = default_settings.copy()
    for key in default_settings:
        settings.setdefault(key, default_settings[key])
    if not settings.get("base_ip") or settings["base_ip"] == "localhost":
        settings["base_ip"] = get_ip()
    return settings

def save_settings(settings):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

def detect_web_ports(ip, port):
    for scheme in ("http", "https"):
        try:
            r = requests.get(f"{scheme}://{ip}:{port}", timeout=1, verify=False)
            if r.status_code:
                return scheme
        except Exception:
            continue
    return None

def get_icon(name):
    name = name.lower()
    if 'nginx' in name: return '/static/icons/nginx.png'
    if 'vaultwarden' in name: return '/static/icons/vaultwarden.png'
    if 'mysql' in name: return '/static/icons/mysql.png'
    return '/static/icons/default.png'

def get_ip():
    try:
        if platform.system() == "Windows":
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

def get_thumbnail_path(name, port):
    return f"static/thumbnails/{name}_{port}.png"

@app.route('/')
def index():
    settings = load_settings()
    containers = []
    others = []
    all_containers = client.containers.list(all=True if settings["show_stopped"] else False)
    for c in all_containers:
        if c.name == "harbormaster":
            continue

        port_data = c.attrs['NetworkSettings']['Ports'] or {}
        ports = []
        for bindings in port_data.values():
            if bindings:
                ports += [b['HostPort'] for b in bindings]

        if not ports and not settings["show_unmapped"]:
            continue

        ip = settings["overrides"].get(c.name, settings["base_ip"])
        web_ports = []
        non_web_ports = []

        for p in ports:
            scheme = detect_web_ports(ip, p)
            if scheme:
                web_ports.append((p, scheme))
            else:
                non_web_ports.append(p)

        icon = get_icon(c.name)

        if web_ports:
            containers.append({'name': c.name, 'ports': web_ports, 'ip': ip, 'icon': icon})
        if non_web_ports:
            others.append({'name': c.name, 'ports': non_web_ports, 'ip': ip, 'icon': icon})

    return render_template_string(DASHBOARD_TEMPLATE, containers=containers, others=others, refresh=settings["auto_refresh_seconds"])

@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    settings = load_settings()
    if request.method == 'POST':
        settings["base_ip"] = request.form.get("base_ip", "localhost")
        settings["auto_refresh_seconds"] = int(request.form.get("auto_refresh_seconds", 10))
        settings["show_stopped"] = "show_stopped" in request.form
        settings["show_unmapped"] = "show_unmapped" in request.form

        overrides = {}
        for name, ip in zip(request.form.getlist("container_name"), request.form.getlist("container_ip")):
            if name.strip() and ip.strip():
                overrides[name.strip()] = ip.strip()
        settings["overrides"] = overrides

        save_settings(settings)
        return redirect('/')
    return render_template_string(SETTINGS_TEMPLATE, settings=settings)

@app.route('/thumbnail/<name>')
def thumbnail(name):
    parts = name.rsplit('_', 1)
    if len(parts) != 2:
        return '', 404
    cname, port = parts

    if cname == "harbormaster":
        return '', 204

    settings = load_settings()
    ip = settings["overrides"].get(cname, settings["base_ip"])
    url = f"http://{ip}:{port}"
    path = get_thumbnail_path(cname, port)

    if not os.path.exists(path):
        if not generate_screenshot(cname, url, path):
            return '', 500

    if not os.path.exists(path):
        return '', 500
    return redirect(f"/{path}")

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
