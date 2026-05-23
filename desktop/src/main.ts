const API_BASE =
  (import.meta.env.VITE_RADAR_API as string | undefined) ??
  "http://127.0.0.1:18765";

const POLL_STATUS_MS = 2500;
const POLL_LOGS_MS = 1500;
const WIDTH = 400;
const HEIGHT_COMPACT = 560;
const HEIGHT_EXPANDED = 728;

type LampState = "idle" | "ok" | "error";

interface LampInfo {
  key: string;
  label: string;
  state: LampState;
  caption: string;
}

interface StatusPayload {
  running: boolean;
  ever_started: boolean;
  ui_expanded: boolean;
  lamps: LampInfo[];
}

const appEl = document.getElementById("app")!;
const heroBtn = document.getElementById("hero-btn") as HTMLButtonElement;
const playIcon = heroBtn.querySelector(".hero__icon--play") as SVGElement;
const stopIcon = heroBtn.querySelector(".hero__icon--stop") as SVGElement;
const lampsEl = document.getElementById("lamps")!;
const logPanel = document.getElementById("log-panel")!;
const logView = document.getElementById("log-view")!;
const btnCollapse = document.getElementById("btn-collapse")!;
const collapsePath = document.getElementById("collapse-path")!;
const btnRefresh = document.getElementById("btn-refresh")!;
const tabButtons = document.querySelectorAll<HTMLButtonElement>(".log-tab");

let running = false;
let logsOpen = false;
let logsCollapsed = false;
let activeTab = "radar.log";
let logPollTimer: ReturnType<typeof setInterval> | null = null;

function isTauri(): boolean {
  return "__TAURI_INTERNALS__" in window;
}

async function resizeWindow(expanded: boolean): Promise<void> {
  if (!isTauri()) return;
  try {
    const { getCurrentWindow } = await import("@tauri-apps/api/window");
    const { LogicalSize } = await import("@tauri-apps/api/dpi");
    const win = getCurrentWindow();
    const h = expanded ? HEIGHT_EXPANDED : HEIGHT_COMPACT;
    await win.setSize(new LogicalSize(WIDTH, h));
  } catch {
    /* preview in browser */
  }
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  const ct = res.headers.get("content-type") ?? "";
  if (ct.includes("application/json")) {
    return res.json() as Promise<T>;
  }
  return res.text() as Promise<T>;
}

function setHeroMode(mode: "play" | "stop"): void {
  heroBtn.classList.toggle("hero--play", mode === "play");
  heroBtn.classList.toggle("hero--stop", mode === "stop");
  heroBtn.setAttribute("aria-label", mode === "play" ? "Запуск" : "Остановить");
  playIcon.toggleAttribute("hidden", mode !== "play");
  stopIcon.toggleAttribute("hidden", mode !== "stop");
}

function renderLamps(lamps: LampInfo[]): void {
  lampsEl.innerHTML = lamps
    .map(
      (l) => `
    <div class="lamp" data-key="${l.key}">
      <span class="lamp__dot lamp__dot--${l.state}"></span>
      <span class="lamp__label">${l.label}</span>
      <span class="lamp__caption">${l.caption || ""}</span>
    </div>`,
    )
    .join("");
}

function setLogsVisible(visible: boolean): void {
  logsOpen = visible;
  logPanel.hidden = !visible;
  appEl.classList.toggle("app--logs-open", visible && !logsCollapsed);
  if (visible) {
    void resizeWindow(true);
    startLogPoll();
  } else {
    void resizeWindow(false);
    stopLogPoll();
  }
}

function setLogsCollapsed(collapsed: boolean): void {
  logsCollapsed = collapsed;
  logPanel.classList.toggle("log-panel--collapsed", collapsed);
  collapsePath.setAttribute(
    "d",
    collapsed ? "M3 2 L7 5 L3 8 Z" : "M2 3 L5 7 L8 3 Z",
  );
  btnCollapse.setAttribute(
    "aria-label",
    collapsed ? "Развернуть логи" : "Свернуть логи",
  );
  appEl.classList.toggle("app--logs-open", logsOpen && !collapsed);
}

function stopLogPoll(): void {
  if (logPollTimer !== null) {
    clearInterval(logPollTimer);
    logPollTimer = null;
  }
}

function startLogPoll(): void {
  stopLogPoll();
  if (!logsOpen || logsCollapsed) return;
  void refreshActiveLog();
  logPollTimer = setInterval(() => void refreshActiveLog(), POLL_LOGS_MS);
}

async function refreshActiveLog(): Promise<void> {
  if (!logsOpen || logsCollapsed) return;
  try {
    if (activeTab === "status") {
      const text = await api<string>("/status-text");
      logView.textContent = text;
      logView.classList.add("log-view--status");
    } else {
      const text = await api<string>(`/logs/${activeTab}`);
      logView.textContent = text;
      logView.classList.remove("log-view--status");
      const atBottom =
        logView.scrollHeight - logView.scrollTop - logView.clientHeight < 24;
      if (atBottom) {
        logView.scrollTop = logView.scrollHeight;
      }
    }
  } catch (err) {
    logView.textContent = `Ошибка API: ${err}\n\nЗапущен ли scripts\\radar_control.py ?`;
  }
}

async function pollStatus(): Promise<void> {
  try {
    const data = await api<StatusPayload>("/status");
    running = data.running;
    renderLamps(data.lamps);
    setHeroMode(running ? "stop" : "play");
    if (running && !logsOpen) {
      setLogsVisible(true);
      setLogsCollapsed(false);
    }
    if (!running && logsOpen) {
      setLogsVisible(false);
      setLogsCollapsed(false);
    }
  } catch {
    /* API offline — keep UI state */
  }
}

async function onHeroClick(): Promise<void> {
  try {
    if (running) {
      await api("/stop", { method: "POST" });
      running = false;
      setHeroMode("play");
      setLogsVisible(false);
      await api("/ui-expanded", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ expanded: false }),
      });
      await pollStatus();
    } else {
      const result = await api<{ ok: boolean; errors?: string[] }>("/start", {
        method: "POST",
      });
      if (!result.ok && result.errors?.length) {
        alert(result.errors.join("\n"));
      }
      await api("/ui-expanded", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ expanded: true }),
      });
      running = true;
      setHeroMode("stop");
      setLogsVisible(true);
      setLogsCollapsed(false);
      await pollStatus();
      await refreshActiveLog();
    }
  } catch (err) {
    alert(`Не удалось связаться с radar_control:\n${err}`);
  }
}

function onTabClick(btn: HTMLButtonElement): void {
  tabButtons.forEach((b) => {
    b.classList.toggle("log-tab--active", b === btn);
    b.setAttribute("aria-selected", b === btn ? "true" : "false");
  });
  activeTab = btn.dataset.tab ?? "radar.log";
  void refreshActiveLog();
}

async function waitForApi(maxMs = 8000): Promise<boolean> {
  const deadline = Date.now() + maxMs;
  while (Date.now() < deadline) {
    try {
      await api<{ ok: boolean }>("/health");
      return true;
    } catch {
      await new Promise((r) => setTimeout(r, 400));
    }
  }
  return false;
}

heroBtn.addEventListener("click", () => void onHeroClick());

btnCollapse.addEventListener("click", () => {
  setLogsCollapsed(!logsCollapsed);
  if (!logsCollapsed) {
    startLogPoll();
  } else {
    stopLogPoll();
  }
});

btnRefresh.addEventListener("click", () => {
  activeTab = "status";
  tabButtons.forEach((b) => {
    const isStatus = b.dataset.tab === "status";
    b.classList.toggle("log-tab--active", isStatus);
    b.setAttribute("aria-selected", isStatus ? "true" : "false");
  });
  if (!logsOpen) {
    setLogsVisible(true);
    setLogsCollapsed(false);
  }
  void refreshActiveLog();
});

tabButtons.forEach((btn) => {
  btn.addEventListener("click", () => onTabClick(btn));
});

void (async () => {
  renderLamps([
    { key: "exchanges", label: "Биржи", state: "idle", caption: "" },
    { key: "tg", label: "TG", state: "idle", caption: "" },
    { key: "join", label: "Join", state: "idle", caption: "" },
  ]);
  setHeroMode("play");
  await resizeWindow(false);

  const ok = await waitForApi();
  if (!ok) {
    lampsEl.insertAdjacentHTML(
      "afterend",
      `<p style="color:var(--color-text-muted);font-size:11px;text-align:center;padding:0 12px 8px">API не отвечает — запустите radar_control</p>`,
    );
  }

  await pollStatus();
  setInterval(() => void pollStatus(), POLL_STATUS_MS);
})();
