const API_BASE =
  (import.meta.env.VITE_RADAR_API as string | undefined) ??
  "http://127.0.0.1:18765";

const POLL_STATUS_MS = 2500;
const POLL_LOGS_MS = 1500;
const CLOSE_STOP_MS = 8000;
const CLOSE_FORCE_DESTROY_MS = 12000;
const WIDTH = 400;
const HEIGHT_COMPACT = 560;
const HEIGHT_EXPANDED = 760;

type LampState = "idle" | "ok" | "error" | "warn";

interface LampInfo {
  key: string;
  label: string;
  state: LampState;
  caption: string;
}

interface LastCycleSource {
  source_id: string;
  downloaded: number;
  new_ids: number;
  to_bot: number;
  filter_skip: number;
  mimo_skip: number;
  dup_skip: number;
  budget_skip: number;
  fetch_error: string;
}

interface LastCyclePayload {
  ts: string;
  sources: Record<string, LastCycleSource>;
  total_to_bot: number;
  misc_errors: string[];
}

interface StatusPayload {
  running: boolean;
  ever_started: boolean;
  ui_expanded: boolean;
  lamps: LampInfo[];
  last_cycle?: LastCyclePayload;
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
const btnMinimize = document.getElementById("btn-minimize");
const btnClose = document.getElementById("btn-close");
const statusBanner = document.getElementById("status-banner");
const tabButtons = document.querySelectorAll<HTMLButtonElement>(".log-tab");

let httpFetch: typeof fetch = globalThis.fetch.bind(globalThis);
let running = false;
let heroBusy = false;
let starting = false;
let pollPaused = false;
let logsOpen = false;
let logsCollapsed = true;
/** true только после клика по стрелке — pollStatus не разворачивает логи сам */
let logsOpenedByUser = false;
let activeTab = "radar.log";
let logPollTimer: ReturnType<typeof setInterval> | null = null;
let statusPollTimer: ReturnType<typeof setInterval> | null = null;
let closingInProgress = false;
let closeDestroyTimer: ReturnType<typeof setTimeout> | null = null;
/** Автоскролл вниз только пока пользователь не прокрутил вверх */
let logFollowBottom = true;

const LOG_SCROLL_BOTTOM_THRESHOLD = 32;

function isTauri(): boolean {
  return "__TAURI_INTERNALS__" in window;
}

function isCanceledError(err: unknown): boolean {
  const msg = String(err).toLowerCase();
  return msg.includes("cancel") || msg.includes("aborted");
}

function showStatus(message: string, tone: "error" | "warn" | "ok" = "warn"): void {
  if (!statusBanner) return;
  statusBanner.textContent = message;
  statusBanner.hidden = false;
  statusBanner.classList.remove(
    "status-banner--error",
    "status-banner--warn",
    "status-banner--ok",
  );
  statusBanner.classList.add(`status-banner--${tone}`);
}

function clearStatus(): void {
  if (!statusBanner) return;
  statusBanner.hidden = true;
  statusBanner.textContent = "";
}

function blockDragOnClick(el: HTMLElement | null): void {
  if (!el) return;
  el.addEventListener("mousedown", (e) => e.stopPropagation());
}

async function initHttpFetch(): Promise<void> {
  if (!isTauri()) return;
  const { fetch: tauriFetch } = await import("@tauri-apps/plugin-http");
  httpFetch = tauriFetch as typeof fetch;
}

function setCloseEnabled(enabled: boolean): void {
  if (btnClose instanceof HTMLButtonElement) {
    btnClose.disabled = !enabled;
  }
}

async function forceDestroyWindow(): Promise<void> {
  if (!isTauri()) return;
  try {
    const { getCurrentWindow } = await import("@tauri-apps/api/window");
    await getCurrentWindow().destroy();
  } catch {
    /* fallback */
    try {
      const { getCurrentWindow } = await import("@tauri-apps/api/window");
      await getCurrentWindow().close();
    } catch {
      /* ignore */
    }
  }
}

async function stopRadarForClose(): Promise<void> {
  pauseStatusPoll();
  stopLogPoll();
  try {
    await apiPost("/stop", "{}", CLOSE_STOP_MS);
  } catch {
    /* таймаут / API недоступен — окно всё равно закрываем */
  }
  running = false;
  starting = false;
  setHeroMode("play");
}

async function requestAppClose(): Promise<void> {
  if (closingInProgress) {
    await forceDestroyWindow();
    return;
  }
  closingInProgress = true;
  setCloseEnabled(false);
  showStatus("Остановка…", "warn");

  if (closeDestroyTimer !== null) {
    clearTimeout(closeDestroyTimer);
  }
  closeDestroyTimer = setTimeout(() => {
    void forceDestroyWindow();
  }, CLOSE_FORCE_DESTROY_MS);

  try {
    await stopRadarForClose();
  } finally {
    if (closeDestroyTimer !== null) {
      clearTimeout(closeDestroyTimer);
      closeDestroyTimer = null;
    }
    await forceDestroyWindow();
    closingInProgress = false;
    setCloseEnabled(true);
  }
}

async function setupWindowChrome(): Promise<void> {
  if (!isTauri()) return;
  try {
    const { getCurrentWindow } = await import("@tauri-apps/api/window");
    const win = getCurrentWindow();
    try {
      await win.setShadow(false);
    } catch {
      /* config shadow:false is primary */
    }
    await win.onCloseRequested((event) => {
      event.preventDefault();
      if (closingInProgress) {
        void forceDestroyWindow();
        return;
      }
      void requestAppClose();
    });
    btnMinimize?.addEventListener("click", (e) => {
      e.preventDefault();
      void win.minimize().catch((err) =>
        showStatus(`Свернуть: ${err}`, "error"),
      );
    });
    btnClose?.addEventListener("click", (e) => {
      e.preventDefault();
      void requestAppClose();
    });
    blockDragOnClick(btnMinimize);
    blockDragOnClick(btnClose);
  } catch (err) {
    showStatus(`Окно Tauri: ${err}`, "error");
  }
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
    /* browser preview */
  }
}

function formatApiError(status: number, text: string): string {
  try {
    const data = JSON.parse(text) as { errors?: string[]; error?: string };
    if (data.errors?.length) return data.errors.join("\n");
    if (data.error) return data.error;
  } catch {
    /* plain text */
  }
  return text || `HTTP ${status}`;
}

async function parseResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(formatApiError(res.status, text));
  }
  const ct = res.headers.get("content-type") ?? "";
  if (ct.includes("application/json")) {
    return res.json() as Promise<T>;
  }
  return res.text() as Promise<T>;
}

/** GET без AbortSignal — иначе Tauri даёт «Request canceled» при параллельных запросах */
async function apiGet<T>(path: string): Promise<T> {
  const res = await httpFetch(`${API_BASE}${path}`);
  return parseResponse<T>(res);
}

function withTimeout<T>(promise: Promise<T>, ms: number, label: string): Promise<T> {
  return Promise.race([
    promise,
    new Promise<T>((_, reject) => {
      setTimeout(
        () => reject(new Error(`Таймаут ${Math.round(ms / 1000)}с — ${label}`)),
        ms,
      );
    }),
  ]);
}

async function apiPost<T>(path: string, body: string, timeoutMs: number): Promise<T> {
  const promise = httpFetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  }).then((res) => parseResponse<T>(res));
  return withTimeout(promise, timeoutMs, path);
}

function pauseStatusPoll(): void {
  pollPaused = true;
  if (statusPollTimer !== null) {
    clearInterval(statusPollTimer);
    statusPollTimer = null;
  }
}

function resumeStatusPoll(): void {
  pollPaused = false;
  if (statusPollTimer !== null) return;
  statusPollTimer = setInterval(() => void pollStatus(), POLL_STATUS_MS);
}

function setHeroMode(mode: "play" | "stop"): void {
  heroBtn.classList.toggle("hero--play", mode === "play");
  heroBtn.classList.toggle("hero--stop", mode === "stop");
  heroBtn.dataset.mode = mode;
  heroBtn.setAttribute("aria-label", mode === "play" ? "Запуск" : "Остановить");
  heroBtn.title = mode === "play" ? "Запуск" : "Остановить";
  playIcon.toggleAttribute("hidden", mode !== "play");
  stopIcon.toggleAttribute("hidden", mode !== "stop");
}

function setHeroBusy(busy: boolean): void {
  heroBusy = busy;
  heroBtn.disabled = busy;
  heroBtn.classList.toggle("hero--busy", busy);
  heroBtn.setAttribute("aria-busy", busy ? "true" : "false");
}

function renderLamps(lamps: LampInfo[]): void {
  lampsEl.innerHTML = lamps
    .map(
      (l) => `
    <div class="lamp" data-key="${l.key}">
      <span class="lamp__dot lamp__dot--${l.state}"></span>
      <span class="lamp__label">${l.label}</span>
    </div>`,
    )
    .join("");
}

function isLogNearBottom(): boolean {
  const gap = logView.scrollHeight - logView.scrollTop - logView.clientHeight;
  return gap <= LOG_SCROLL_BOTTOM_THRESHOLD;
}

function scrollLogToBottom(force = false): void {
  if (!force && !logFollowBottom) return;
  if (force) logFollowBottom = true;
  requestAnimationFrame(() => {
    logView.scrollTop = logView.scrollHeight;
    requestAnimationFrame(() => {
      logView.scrollTop = logView.scrollHeight;
    });
  });
}

async function setLogsVisible(
  visible: boolean,
  opts?: { user?: boolean },
): Promise<void> {
  if (opts?.user) {
    logsOpenedByUser = visible;
  }
  logsOpen = visible;
  logPanel.hidden = !visible;
  if (visible) {
    logPanel.removeAttribute("hidden");
  } else {
    logPanel.setAttribute("hidden", "");
  }
  appEl.classList.toggle("app--logs-open", visible && !logsCollapsed);
  await resizeWindow(visible && !logsCollapsed);
  if (visible && !logsCollapsed) {
    startLogPoll();
    scrollLogToBottom(true);
  } else {
    stopLogPoll();
  }
}

function setLogsCollapsed(collapsed: boolean): void {
  logsCollapsed = collapsed;
  logPanel.classList.toggle("log-panel--collapsed", collapsed);
  collapsePath.setAttribute(
    "d",
    collapsed ? "M2 3 L5 7 L8 3 Z" : "M2 7 L5 3 L8 7 Z",
  );
  btnCollapse.setAttribute(
    "aria-label",
    collapsed ? "Развернуть логи" : "Свернуть логи",
  );
  appEl.classList.toggle("app--logs-open", logsOpen && !collapsed);
  void resizeWindow(logsOpen && !logsCollapsed);
  if (!collapsed && logsOpen) {
    startLogPoll();
    scrollLogToBottom(true);
  } else {
    stopLogPoll();
  }
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

const MAX_LOG_CHARS = 100_000;

function trimLogText(text: string): string {
  if (text.length <= MAX_LOG_CHARS) return text;
  return `… (последние ${MAX_LOG_CHARS} символов)\n${text.slice(-MAX_LOG_CHARS)}`;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderStatusHtml(text: string): string {
  return text.split(/\r?\n/).map((line) => {
    if (!line.trim()) {
      return '<div class="status-line status-line--blank"></div>';
    }
    const colon = line.indexOf(":");
    if (colon > 0 && colon < 56) {
      const key = line.slice(0, colon).trim();
      const value = line.slice(colon + 1).trimStart();
      const indent = line.startsWith("  ") ? " status-line--indent" : "";
      return (
        `<div class="status-line${indent}">` +
        `<span class="status-line__key">${escapeHtml(key)}</span>` +
        `<span class="status-line__value">${escapeHtml(value)}</span>` +
        `</div>`
      );
    }
    return (
      `<div class="status-line status-line--full">` +
      `<span class="status-line__value">${escapeHtml(line)}</span>` +
      `</div>`
    );
  }).join("");
}

async function refreshActiveLog(): Promise<void> {
  if (!logsOpen || logsCollapsed || pollPaused) return;
  const follow = logFollowBottom;
  const savedScrollTop = logView.scrollTop;
  try {
    if (activeTab === "status") {
      const text = trimLogText(await apiGet<string>("/status-text"));
      logView.innerHTML = renderStatusHtml(text);
      logView.classList.add("log-view--status");
    } else {
      const text = trimLogText(await apiGet<string>(`/logs/${activeTab}`));
      logView.textContent = text;
      logView.classList.remove("log-view--status");
    }
    if (follow) {
      scrollLogToBottom();
    } else {
      requestAnimationFrame(() => {
        const maxTop = Math.max(0, logView.scrollHeight - logView.clientHeight);
        logView.scrollTop = Math.min(savedScrollTop, maxTop);
      });
    }
  } catch (err) {
    if (isCanceledError(err)) return;
    logView.textContent = `Ошибка API: ${err}\n\nЗапущен ли scripts\\radar_control.py ?`;
    if (follow) {
      scrollLogToBottom();
    } else {
      requestAnimationFrame(() => {
        const maxTop = Math.max(0, logView.scrollHeight - logView.clientHeight);
        logView.scrollTop = Math.min(savedScrollTop, maxTop);
      });
    }
  }
}

async function pollStatus(): Promise<void> {
  if (pollPaused || heroBusy || starting) return;
  try {
    const data = await apiGet<StatusPayload>("/status");
    running = data.running;
    renderLamps(data.lamps);
    setHeroMode(running ? "stop" : "play");
    if (running && logsOpen && !logsOpenedByUser) {
      void setLogsVisible(false);
    }
    if (
      running &&
      data.ui_expanded &&
      !logsOpenedByUser &&
      isTauri()
    ) {
      void apiPost(
        "/ui-expanded",
        JSON.stringify({ expanded: false }),
        15000,
      ).catch(() => {});
    }
    if (!running && logsOpen && !starting && !heroBusy) {
      void setLogsVisible(false);
      logsOpenedByUser = false;
      setLogsCollapsed(true);
    }
    if (logsOpen && !logsCollapsed) {
      void refreshActiveLog();
    }
  } catch (err) {
    if (isCanceledError(err) || heroBusy || starting) return;
    showStatus(`API /status: ${err}`, "warn");
  }
}

async function runStart(): Promise<void> {
  pauseStatusPoll();
  try {
    const result = await apiPost<{ ok: boolean; errors?: string[] }>(
      "/start",
      "{}",
      120000,
    );
    if (!result.ok) {
      showStatus(result.errors?.join("\n") ?? "Старт не удался", "error");
      running = false;
      setHeroMode("play");
      await setLogsVisible(false);
      return;
    }
    await apiPost(
      "/ui-expanded",
      JSON.stringify({ expanded: false }),
      15000,
    );
    clearStatus();
    logsOpenedByUser = false;
    await setLogsVisible(false);
    await pollStatus();
  } catch (err) {
    if (!isCanceledError(err)) {
      running = false;
      setHeroMode("play");
      showStatus(`Радар: ${err}`, "error");
      logsOpenedByUser = false;
      await setLogsVisible(false);
    }
  } finally {
    starting = false;
    resumeStatusPoll();
  }
}

async function onHeroClick(): Promise<void> {
  if (heroBusy || starting) return;

  if (running) {
    setHeroBusy(true);
    pauseStatusPoll();
    stopLogPoll();
    try {
      showStatus("Остановка…", "warn");
      await apiPost("/stop", "{}", 60000);
      running = false;
      setHeroMode("play");
      logsOpenedByUser = false;
      await setLogsVisible(false);
      await apiPost("/ui-expanded", JSON.stringify({ expanded: false }), 15000);
      clearStatus();
      await pollStatus();
    } catch (err) {
      if (!isCanceledError(err)) {
        showStatus(`Стоп: ${err}`, "error");
      }
    } finally {
      setHeroBusy(false);
      resumeStatusPoll();
    }
    return;
  }

  starting = true;
  running = true;
  setHeroMode("stop");
  logsOpenedByUser = false;
  setLogsCollapsed(true);
  await setLogsVisible(false);
  showStatus("Запуск…", "warn");
  void runStart();
}

function onTabClick(btn: HTMLButtonElement): void {
  tabButtons.forEach((b) => {
    b.classList.toggle("log-tab--active", b === btn);
    b.setAttribute("aria-selected", b === btn ? "true" : "false");
  });
  activeTab = btn.dataset.tab ?? "radar.log";
  logFollowBottom = true;
  void refreshActiveLog();
}

async function waitForApi(maxMs = 8000): Promise<boolean> {
  const deadline = Date.now() + maxMs;
  while (Date.now() < deadline) {
    try {
      await apiGet<{ ok: boolean }>("/health");
      return true;
    } catch {
      await new Promise((r) => setTimeout(r, 400));
    }
  }
  return false;
}

heroBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  void onHeroClick();
});

btnCollapse.addEventListener("click", () => {
  if (!logsOpen) {
    logsOpenedByUser = true;
    setLogsCollapsed(false);
    void setLogsVisible(true, { user: true });
    if (isTauri()) {
      void apiPost(
        "/ui-expanded",
        JSON.stringify({ expanded: true }),
        15000,
      ).catch(() => {});
    }
    return;
  }
  logsOpenedByUser = false;
  setLogsCollapsed(true);
  void setLogsVisible(false);
  if (isTauri()) {
    void apiPost(
      "/ui-expanded",
      JSON.stringify({ expanded: false }),
      15000,
    ).catch(() => {});
  }
});

tabButtons.forEach((btn) => {
  btn.addEventListener("click", () => onTabClick(btn));
});

void (async () => {
  try {
    await initHttpFetch();
  } catch (err) {
    showStatus(`HTTP plugin: ${err}`, "error");
  }
  await setupWindowChrome();
  blockDragOnClick(heroBtn);
  blockDragOnClick(btnCollapse);
  tabButtons.forEach((btn) => blockDragOnClick(btn));
  logView.addEventListener(
    "scroll",
    () => {
      logFollowBottom = isLogNearBottom();
    },
    { passive: true },
  );

  renderLamps([
    { key: "exchanges", label: "Биржи", state: "idle", caption: "" },
    { key: "tg", label: "TG", state: "idle", caption: "" },
  ]);
  setHeroMode("play");
  await resizeWindow(false);

  const ok = await waitForApi();
  if (!ok) {
    showStatus(
      "API не отвечает. Запустите start-radar-desktop.vbs",
      "error",
    );
  } else {
    clearStatus();
  }

  await pollStatus();
  resumeStatusPoll();
})();
