from flask import Flask, render_template, request, redirect, send_file
import docker, json, os, socket, subprocess, requests, platform

app = Flask(__name__, template_folder="templates")
client = docker.DockerClient(base_url='unix://var/run/docker.sock')
SETTINGS_FILE = '/data/settings.json'

default_settings = {
    "base_ip": "",
    "auto_refresh_seconds": 10,
    "show_stopped": False,
    "show_unmapped": False,
    "overrides": {},
    "sort_by": "name"
}

def get_host_ip():
    try:
        if platform.system() == "Windows":
            return socket.gethostbyname(socket.gethostname())
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

def port_has_http(ip, port):
    try:
        return requests.get(f"http://{ip}:{port}", timeout=2).ok
    except Exception:
        return False

def port_has_https(ip, port):
    try:
        return requests.get(f"https://{ip}:{port}", timeout=2, verify=False).ok
    except Exception:
        return False

def get_icon_for_service(image):
    icon_map = {
        'postgres': 'postgresql',
        'portainer': 'portainer',
        'vaultwarden': 'bitwarden',
        'mariadb': 'mariadb',
        'mysql': 'mysql',
        'redis': 'redis',
        'nginx': 'nginx'
    }
    image = image.lower()
    for key in icon_map:
        if key in image:
            return f"https://cdn.simpleicons.org/{icon_map[key]}"
    return "/static/icons/generic.png"

def load_settings():
    settings = default_settings.copy()
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            settings.update(json.load(f))
    if not settings.get("base_ip") or settings["base_ip"] == "localhost":
        settings["base_ip"] = get_host_ip()
    return settings

def save_settings(data):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_thumbnail_path(name, port):
    return os.path.join(app.root_path, "static", "thumbnails", f"{name}_{port}.png")

def run_screenshot_script(name, url, path):
    log_path = os.path.join(app.root_path, "screenshot.log")
    try:
        with open(log_path, "a") as log:
            log.write(f">>> RUN: python3 screenshot.py {name} {url}\n")
        result = subprocess.run(
            ["python3", "screenshot.py", name, url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="/app"
        )
        with open(log_path, "a") as log:
            log.write(f"Exit code: {result.returncode}\n")
            log.write("STDOUT:\n" + result.stdout + "\n")
            log.write("STDERR:\n" + result.stderr + "\n")
        return result.returncode == 0 and os.path.exists(path)
    except Exception as e:
        with open(log_path, "a") as log:
            log.write("EXCEPTION: " + str(e) + "\n")
        return False

def build_container_data(settings):
    containers = []
    all_containers = sorted(
        client.containers.list(all=settings["show_stopped"]),
        key=lambda c: c.name.lower()
    )
    for c in all_containers:
        if c.name == "harbormaster":
            continue

        port_data = c.attrs['NetworkSettings']['Ports'] or {}
        ports = []
        for bindings in port_data.values():
            if bindings:
                ports += [b['HostPort'] for b in bindings if 'HostPort' in b]
        ports = list(set(ports))

        if not ports and not settings["show_unmapped"]:
            continue

        ip = settings["overrides"].get(c.name, settings["base_ip"])
        web_ports = []
        non_web_ports = []

        for p in ports:
            scheme = None
            if port_has_https(ip, p):
                scheme = "https"
            elif port_has_http(ip, p):
                scheme = "http"

            if scheme:
                web_ports.append((p, scheme))
            else:
                non_web_ports.append(p)

        image_name = c.image.tags[0] if c.image.tags else c.image.short_id
        icon = get_icon_for_service(image_name)

        containers.append({
            'name': c.name,
            'image': image_name,
            'web_ports': web_ports,
            'other_ports': non_web_ports,
            'ip': ip,
            'icon': icon,
            'status': c.status
        })

    sort_by = settings.get("sort_by", "name")

    def sort_key(c):
        if sort_by == "status":
            return c["status"]
        elif sort_by == "ports":
            return len(c["web_ports"]) + len(c["other_ports"])
        elif sort_by == "image":
            return c["image"].lower()
        return c["name"].lower()

    return sorted(containers, key=sort_key)

@app.route('/')
def index():
    settings = load_settings()
    containers = build_container_data(settings)
    return render_template("dashboard.html", containers=containers, settings=settings)

@app.route('/grid')
def container_grid():
    settings = load_settings()
    containers = build_container_data(settings)
    return render_template("_grid.html", containers=containers)

@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    current = load_settings()
    if request.method == 'POST':
        # sort, base_ip, auto-refresh
        current["sort_by"] = request.form.get("sort_by", current.get("sort_by", "name"))
        current["base_ip"] = request.form.get("base_ip", current["base_ip"])
        current["auto_refresh_seconds"] = int(request.form.get("auto_refresh_seconds", current["auto_refresh_seconds"]))
        current["show_stopped"] = "show_stopped" in request.form
        current["show_unmapped"] = "show_unmapped" in request.form

        # inline container IP override (single entry update)
        if "container_name" in request.form and "container_ip" in request.form:
            name = request.form.get("container_name").strip()
            ip = request.form.get("container_ip").strip()
            if name and ip:
                current["overrides"][name] = ip

        # batch update from legacy settings form
        elif "container_name[]" in request.form and "container_ip[]" in request.form:
            overrides = {}
            for name, ip in zip(request.form.getlist("container_name[]"), request.form.getlist("container_ip[]")):
                if name.strip() and ip.strip():
                    overrides[name.strip()] = ip.strip()
            current["overrides"] = overrides

        save_settings(current)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return '', 204
        return redirect('/')
    return render_template("settings.html", settings=current)

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
        if not (port_has_http(ip, port) or port_has_https(ip, port)):
            return '', 204
        if not run_screenshot_script(f"{cname}_{port}", url, path):
            return "[500] Subprocess failed to generate screenshot", 500

    if not os.path.exists(path):
        return "[500] Screenshot file missing after subprocess", 500

    try:
        return send_file(path, mimetype='image/png')
    except Exception as e:
        print(f"[ERROR] Failed to send file: {e}")
        return f"[500] Send file error: {e}", 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
