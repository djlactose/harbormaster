function setTheme(theme) {
  document.body.classList.toggle('dark', theme === 'dark');
  document.cookie = `theme=${theme}; path=/; max-age=31536000`;
}
function getTheme() {
  const match = document.cookie.match(/theme=(dark|light)/);
  return match ? match[1] : (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
}
function setCookie(name, value, days = 365) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${value}; path=/; expires=${expires}`;
}
function getCookie(name) {
  return document.cookie.split('; ').find(r => r.startsWith(name + '='))?.split('=')[1];
}
function debounce(fn, delay = 300) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

function filterContainers() {
  const val = document.getElementById("filterInput").value.toLowerCase();
  document.querySelectorAll(".container-card").forEach(card => {
    const name = card.querySelector("strong").innerText.toLowerCase();
    card.style.display = name.includes(val) ? "" : "none";
  });
}
function filterOnlyWebContainers(enabled) {
  document.querySelectorAll('.container-card').forEach(card => {
    const hasWeb = card.getAttribute('data-has-web') === 'yes';
    card.style.display = (enabled && !hasWeb) ? 'none' : '';
  });
}
function initOnlyWebFilter() {
  const saved = getCookie("onlyWeb") === "1";
  document.getElementById("toggleOnlyWeb").checked = saved;
  filterOnlyWebContainers(saved);
}
function postToggleSettings() {
  const form = new URLSearchParams();
  if (document.getElementById("toggleStopped").checked) form.set("show_stopped", "on");
  if (document.getElementById("toggleUnmapped").checked) form.set("show_unmapped", "on");
  fetch("/settings", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded", "X-Requested-With": "XMLHttpRequest" },
    body: form.toString()
  }).then(() => setTimeout(refreshContainerGrid, 300));
}
function saveBaseIp() {
  const baseIp = document.getElementById("baseIpInput").value;
  const form = new URLSearchParams();
  form.set("base_ip", baseIp);
  fetch("/settings", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded", "X-Requested-With": "XMLHttpRequest" },
    body: form.toString()
  }).then(() => refreshContainerGrid());
}
function refreshContainerGrid() {
  const container = document.querySelector(".container-grid");
  container.classList.add("fade-out");
  fetch("/grid")
    .then(response => response.text())
    .then(html => {
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");
      const newGrid = doc.querySelector(".container-grid");
      container.replaceWith(newGrid);
      filterContainers();
      filterOnlyWebContainers(document.getElementById("toggleOnlyWeb").checked);
    })
    .finally(() => {
      setTimeout(() => {
        const updated = document.querySelector(".container-grid");
        updated.classList.remove("fade-out");
      }, 50);
    });
}
function editIp(el) {
  const card = el.closest('.container-card');
  card.querySelector('.ip-display').style.display = 'none';
  card.querySelector('.ip-edit').style.display = 'none';
  card.querySelector('.ip-input').style.display = 'flex';
}
function cancelIp(btn) {
  const group = btn.closest('.ip-input');
  const card = btn.closest('.container-card');
  group.style.display = 'none';
  card.querySelector('.ip-display').style.display = '';
  card.querySelector('.ip-edit').style.display = '';
}
function saveIp(btn) {
  const card = btn.closest('.container-card');
  const name = card.getAttribute('data-container');
  const ip = card.querySelector('.ip-input input').value;
  const form = new URLSearchParams();
  form.set("container_name", name);
  form.set("container_ip", ip);
  fetch("/settings", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded", "X-Requested-With": "XMLHttpRequest" },
    body: form.toString()
  }).then(() => refreshContainerGrid());
}

document.addEventListener("DOMContentLoaded", () => {
  const savedTheme = getTheme();
  setTheme(savedTheme);
  document.getElementById("toggleDark").checked = savedTheme === 'dark';

  document.getElementById("toggleStopped").addEventListener("change", debounce(postToggleSettings, 300));
  document.getElementById("toggleUnmapped").addEventListener("change", debounce(postToggleSettings, 300));
  document.getElementById("toggleOnlyWeb").addEventListener("change", () => {
    const checked = document.getElementById("toggleOnlyWeb").checked;
    setCookie("onlyWeb", checked ? "1" : "0");
    filterOnlyWebContainers(checked);
  });
  document.getElementById("toggleDark").addEventListener("change", function () {
    setTheme(this.checked ? 'dark' : 'light');
  });
  document.getElementById("sortOrder")?.addEventListener("change", function () {
    const form = new URLSearchParams();
    form.set("sort_by", this.value);
    fetch("/settings", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded", "X-Requested-With": "XMLHttpRequest" },
      body: form.toString()
    }).then(() => refreshContainerGrid());
  });

  // auto-refresh countdown
  let countdownEl = document.getElementById("countdownText");
  let dropdown = document.getElementById("refreshSelect");
  let refreshRate = parseInt(getCookie("refreshRate") || dropdown?.value || "10");
  let timeLeft = refreshRate;
  dropdown.value = refreshRate;

  setInterval(() => {
    if (refreshRate > 0) {
      timeLeft--;
      if (timeLeft <= 0) {
        refreshContainerGrid();
        timeLeft = refreshRate;
      }
      countdownEl.textContent = `Refreshing in ${timeLeft}s`;
    } else {
      countdownEl.textContent = "Auto-refresh is off";
    }
  }, 1000);

  dropdown.addEventListener("change", function () {
    refreshRate = parseInt(this.value);
    timeLeft = refreshRate;
    setCookie("refreshRate", refreshRate);
    const form = new URLSearchParams();
    form.set("auto_refresh_seconds", refreshRate);
    fetch("/settings", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded", "X-Requested-With": "XMLHttpRequest" },
      body: form.toString()
    });
  });

  initOnlyWebFilter();
});
