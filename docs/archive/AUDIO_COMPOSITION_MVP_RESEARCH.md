# MVP автокомпоновки музыки под хронометраж (TuneBlades-like, без ML)

**Дата:** 2026-05-25  
**Стек:** Python 3.11, Librosa 0.11+, FFmpeg 6+, FastAPI  
**Цель:** детерминированное сокращение/перестройка трека под `Target_Time` с ритмически выровненными склейками и 3–5 вариантами результата.

**Связанные работы (для ориентира, не обязательны в MVP):** Ellis DP beat tracking; Foote checkerboard novelty + SSM; McFee–Ellis Laplacian segmentation; Disney Research «Scalable Music» (seam-carving + DP path); Stoller et al. structure-aware rearrangement (2023).

---

## Оглавление

1. [Математика и анализ звука (Librosa)](#1-математика-и-анализ-звука-librosa)
2. [Алгоритм компоновки](#2-алгоритм-компоновки-поиск-точек-реза)
3. [Инженерия склейки и кроссфейдов (FFmpeg)](#3-инженерия-склейки-и-кроссфейдов-ffmpeg)
4. [Архитектура API (FastAPI)](#4-архитектура-api-fastapi-и-производительность)
5. [Чек-лист для заказчика (10 вопросов Да/Нет)](#5-чек-лист-для-заказчика)
6. [Рекомендуемая структура репозитория MVP](#6-рекомендуемая-структура-репозитория-mvp)

---

## 1. Математика и анализ звука (Librosa)

### 1.1. Пайплайн «стабильный BPM + сетка ударов»

**Проблема:** один вызов `beat_track()` на «плохом» материале (живой джаз, рубленый рок, rubato) даёт смещённый глобальный tempo и пропуски/лишние доли.

**Рекомендуемая цепочка (многоступенчатая, детерминированная):**

| Шаг | Действие | Зачем |
|-----|----------|-------|
| A | Загрузка mono, `sr=22050` (или 44100 для финала) | Единая шкала кадров |
| B | Onset strength envelope | База для beat и onset |
| C | Оценка tempo (несколько методов + голосование) | Стабильный `bpm` для DP |
| D | `beat_track(onset_envelope=..., bpm=...)` | Глобальная сетка |
| E | Квантизация к тактам + downbeat (опционально) | Склейки на 1-ю долю |
| F | Валидация IOI (inter-onset interval) | Отсев «плывущей» сетки |

```python
"""
analysis/beats.py — стабильная сетка ударов для MVP.
Зависимости: librosa>=0.10, numpy, scipy
"""
from __future__ import annotations

import numpy as np
import librosa


def load_mono(path: str, sr: int = 22050) -> tuple[np.ndarray, int]:
    y, sr_out = librosa.load(path, sr=sr, mono=True)
    return y, sr_out


def onset_envelope(y: np.ndarray, sr: int, hop_length: int = 512) -> np.ndarray:
    # median по каналам не нужен для mono; aggregate полезен для стерео-источника
    return librosa.onset.onset_strength(
        y=y,
        sr=sr,
        hop_length=hop_length,
        aggregate=np.median,
        center=True,
    )


def estimate_bpm_candidates(
    onset_env: np.ndarray,
    sr: int,
    hop_length: int = 512,
) -> list[float]:
    """Несколько оценок tempo → медиана / фильтр выбросов."""
    # 1) Классическая autocorrelation tempo
    tempo_static = librosa.feature.tempo(
        onset_envelope=onset_env, sr=sr, hop_length=hop_length, aggregate=np.median
    )
    # 2) PLP-подобная оценка через beat_track с разными start_bpm
    candidates = [float(np.atleast_1d(tempo_static)[0])]
    for start in (90.0, 120.0, 140.0):
        t, _ = librosa.beat.beat_track(
            onset_envelope=onset_env, sr=sr, hop_length=hop_length, start_bpm=start, trim=True
        )
        if t > 0:
            candidates.append(float(t))
    # Удаляем дубликаты около ±3 BPM
    candidates = sorted(candidates)
    filtered: list[float] = []
    for c in candidates:
        if not filtered or abs(c - filtered[-1]) > 3.0:
            filtered.append(c)
    return filtered


def pick_best_bpm(
    y: np.ndarray,
    sr: int,
    onset_env: np.ndarray,
    hop_length: int = 512,
) -> tuple[float, np.ndarray]:
    """
    Выбираем BPM, у которого beat_track даёт наиболее «ровную» сетку IOI.
    Метрика: низкий коэффициент вариации интервалов между beat (в секундах).
    """
    best_bpm, best_beats, best_cv = 120.0, np.array([]), np.inf
    for bpm in estimate_bpm_candidates(onset_env, sr, hop_length):
        _, beats_frames = librosa.beat.beat_track(
            onset_envelope=onset_env,
            sr=sr,
            hop_length=hop_length,
            bpm=bpm,
            trim=True,
            units="frames",
        )
        if len(beats_frames) < 8:
            continue
        beat_times = librosa.frames_to_time(beats_frames, sr=sr, hop_length=hop_length)
        ioi = np.diff(beat_times)
        if len(ioi) < 2:
            continue
        cv = float(np.std(ioi) / (np.mean(ioi) + 1e-9))
        if cv < best_cv:
            best_cv, best_bpm, best_beats = cv, bpm, beats_frames
    if len(best_beats) == 0:
        tempo, best_beats = librosa.beat.beat_track(
            y=y, sr=sr, hop_length=hop_length, trim=False, units="frames"
        )
        best_bpm = float(tempo)
    beat_times = librosa.frames_to_time(best_beats, sr=sr, hop_length=hop_length)
    return best_bpm, beat_times


def beats_with_dynamic_tempo(
    y: np.ndarray,
    sr: int,
    hop_length: int = 512,
) -> tuple[float, np.ndarray]:
    """
    Fallback для сильного rubato: time-varying bpm в beat_track.
    Документация: librosa auto_example plot_dynamic_beat.
    """
    onset_env = onset_envelope(y, sr, hop_length)
    tempo_dynamic = librosa.feature.tempo(
        onset_envelope=onset_env,
        sr=sr,
        hop_length=hop_length,
        aggregate=None,  # вектор по кадрам
        std_bpm=4.0,     # шире prior при дрейфе темпа
    )
    tempo_global, beats = librosa.beat.beat_track(
        onset_envelope=onset_env,
        sr=sr,
        hop_length=hop_length,
        bpm=tempo_dynamic,
        trim=False,
        units="time",
    )
    return float(tempo_global), beats


def quantize_to_bars(
    beat_times: np.ndarray,
    bpm: float,
    beats_per_bar: int = 4,
    phase_offset_beats: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """
    beat_times → bar_starts (границы тактов).
    phase_offset_beats: сдвиг, какая доля считается «1» (0 = первый beat = downbeat).
    """
    if len(beat_times) < beats_per_bar:
        return beat_times.copy(), beat_times.copy()
    bar_starts = beat_times[phase_offset_beats::beats_per_bar]
    # Последний неполный такт: не используем как cut, если < 1 bar
    return beat_times, bar_starts
```

**Гарантии «насколько можно»:**

- **100% стабильный BPM** существует только у клика/электроники с фиксированным темпом. Для остального — **рабочий глобальный BPM** + допуск ±1–2% на долю.
- **Beat positions** — результат DP (Ellis): оптимальная последовательность пиков onset envelope при штрафе за отклонение от периода `60/bpm` сек.
- Для **сильного rubato** переключайтесь на `beats_with_dynamic_tempo()` или `librosa.beat.plp()` (локально устойчивый pulse).

```python
def beat_grid_plp_fallback(y: np.ndarray, sr: int, hop_length: int = 512) -> np.ndarray:
    onset_env = onset_envelope(y, sr, hop_length)
    pulse = librosa.beat.plp(onset_envelope=onset_env, sr=sr, hop_length=hop_length)
    peaks = librosa.util.localmax(pulse) * librosa.util.peak_pick(
        pulse, pre_max=3, post_max=3, pre_avg=3, post_avg=5, delta=0.05, wait=10
    )
    # Упрощённо: localmax + минимальный интервал в кадрах от BPM
    beat_frames = np.flatnonzero(librosa.util.localmax(pulse))
    return librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop_length)
```

---

### 1.2. Fallback при «плывущей» сетке и ложных онсетах

#### A. Динамический порог для onset peak picking

`librosa.onset.onset_detect` по умолчанию использует `delta` и `wait`. Для живых записей лучше **адаптивный delta** от локальной статистики envelope:

```python
def onset_detect_adaptive(
    onset_env: np.ndarray,
    sr: int,
    hop_length: int = 512,
    wait_ms: float = 30.0,
) -> np.ndarray:
    """
    wait_ms: минимальное расстояние между онсетами (мс) — отсекает дробление одной ноты.
    delta: rolling median + k * MAD.
    """
    win = max(5, int(0.15 * sr / hop_length))  # ~150 ms окно
    med = scipy.ndimage.median_filter(onset_env, size=win)
    mad = scipy.ndimage.median_filter(np.abs(onset_env - med), size=win) + 1e-6
    dynamic_delta = med + 1.5 * mad

    onset_frames = []
    last = -10_000
    wait_frames = int(wait_ms / 1000.0 * sr / hop_length)
    for i in range(1, len(onset_env) - 1):
        if onset_env[i] > dynamic_delta[i] and onset_env[i] > onset_env[i - 1] and onset_env[i] >= onset_env[i + 1]:
            if i - last >= wait_frames:
                onset_frames.append(i)
                last = i
    return librosa.frames_to_time(np.array(onset_frames), sr=sr, hop_length=hop_length)
```

Импорт: `import scipy.ndimage` (или чистый numpy rolling).

#### B. Фильтрация ложных beats по IOI

```python
def filter_beats_by_ioi(
    beat_times: np.ndarray,
    bpm: float,
    tolerance: float = 0.08,
) -> np.ndarray:
    """Удаляем beats, чей IOI выбивается из [expected*(1±tol)]."""
    if len(beat_times) < 3:
        return beat_times
    expected = 60.0 / bpm
    kept = [beat_times[0]]
    for t in beat_times[1:]:
        ioi = t - kept[-1]
        if (1.0 - tolerance) * expected <= ioi <= (1.0 + tolerance) * expected:
            kept.append(t)
        elif ioi > (1.0 + tolerance) * expected:
            # пропущенный удар — вставляем синтетический только если > 1.5 expected
            if ioi < 1.75 * expected:
                kept.append(t)
    return np.array(kept)
```

#### C. Стратегии fallback (дерево решений)

```
1. beat_track + голосование BPM + IOI filter
   └─ CV(IOI) > 0.12 ? → 2
2. dynamic tempo (feature.tempo aggregate=None) + beat_track
   └─ всё ещё плохо ? → 3
3. PLP localmax
   └─ всё ещё плохо ? → 4
4. Onset-only grid: квантизация onset_detect к ближайшему expected IOI
   └─ предупреждение клиенту: «ритмическая склейка degraded»
```

#### D. Onset backtrack (точная фаза удара)

Для **склейки** важна не только сетка beat, а **фаза** внутри периода. После выбора кадра beat/onset:

```python
def refine_cut_to_onset(
    y: np.ndarray,
    sr: int,
    rough_time: float,
    window_sec: float = 0.05,
) -> float:
    """Сдвиг cut к ближайшему onset в окне ±window_sec."""
    hop = 512
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    onsets = librosa.onset.onset_detect(
        onset_envelope=onset_env, sr=sr, hop_length=hop, units="time", backtrack=True
    )
    if len(onsets) == 0:
        return rough_time
    idx = np.argmin(np.abs(onsets - rough_time))
    if abs(onsets[idx] - rough_time) <= window_sec:
        return float(onsets[idx])
    return rough_time
```

---

### 1.3. Structural Segmentation (фразы, не отдельные удары)

**Принцип MVP:** режем на границах **сегментов** (куплет/припев/бридж), внутри сегмента — только **целые такты** или **2/4/8 такта**.

#### Метод 1: Novelty на Self-Similarity Matrix (Foote)

```python
def checkerboard_kernel(L: int) -> np.ndarray:
    """L = полуразмер окна; размер ядра M = 2L+1."""
    M = 2 * L + 1
    k = np.zeros((M, M), dtype=np.float32)
    k[:L, :L] = 1
    k[L + 1 :, L + 1 :] = 1
    k[:L, L + 1 :] = -1
    k[L + 1 :, :L] = -1
    return k


def novelty_foote(ssm: np.ndarray, L: int = 16) -> np.ndarray:
    """ssm: NxN affinity matrix, нормированная [0,1]."""
    N = ssm.shape[0]
    k = checkerboard_kernel(L)
    M = k.shape[0]
    novelty = np.zeros(N, dtype=np.float32)
    for i in range(L, N - L):
        patch = ssm[i - L : i + L + 1, i - L : i + L + 1]
        if patch.shape[0] == M:
            novelty[i] = float(np.sum(patch * k) / (M * M))
    novelty = np.maximum(novelty, 0)
    return novelty


def structural_segments_foote(
    y: np.ndarray,
    sr: int,
    hop_length: int = 512,
    n_segments: int | None = None,
) -> list[dict]:
    """
    Возвращает список сегментов: {start, end, label} в секундах.
    """
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)
    chroma_stack = librosa.feature.stack_memory(chroma, n_steps=10, delay=3)
    R = librosa.segment.recurrence_matrix(
        chroma_stack, mode="affinity", sym=True, metric="cosine", width=3, self=True
    )
    Rf = librosa.segment.path_enhance(R, n=51, window="hann", n_filters=7, zero_mean=True)
    # Нормализация
    Rf = (Rf - Rf.min()) / (Rf.max() - Rf.min() + 1e-9)
    nov = novelty_foote(Rf, L=16)
    # Пики novelty → границы (минимальное расстояние в кадрах)
    min_dist = int(4.0 * sr / hop_length)  # ~4 с между границами
    peaks = librosa.util.peak_pick(
        nov, pre_max=min_dist // 2, post_max=min_dist // 2,
        pre_avg=min_dist, post_avg=min_dist, delta=0.05, wait=min_dist
    )
    boundary_frames = [0] + list(peaks) + [len(nov) - 1]
    boundary_times = librosa.frames_to_time(boundary_frames, sr=sr, hop_length=hop_length)
    segments = []
    for i in range(len(boundary_times) - 1):
        segments.append({
            "start": float(boundary_times[i]),
            "end": float(boundary_times[i + 1]),
            "label": f"S{i}",
        })
    if n_segments and len(segments) > n_segments:
        # Объединить соседние с наименьшей novelty на границе — опустим детали MVP
        pass
    return segments
```

#### Метод 2: Laplacian segmentation (McFee–Ellis, в librosa example)

Используйте beat-synchronous chroma + `scipy.linalg.eigh(L)` + k-means на eigenvectors — даёт **музыкально осмысленные** кластеры. Для MVP достаточно **5–8 сегментов** на трек 3–5 мин.

#### Метод 3: Простой энергетический fallback

```python
def segments_by_energy(y: np.ndarray, sr: int, n_bands: int = 6) -> list[dict]:
    rms = librosa.feature.rms(y=y)[0]
    times = librosa.times_like(rms, sr=sr)
    # Агрегировать в n_bands квантилей по времени
    edges = np.quantile(np.arange(len(rms)), np.linspace(0, 1, n_bands + 1)).astype(int)
    edges = np.unique(edges)
    segs = []
    for i in range(len(edges) - 1):
        segs.append({"start": float(times[edges[i]]), "end": float(times[edges[i + 1]]), "label": f"E{i}"})
    return segs
```

#### Синхронизация структуры с тактами

```python
def snap_segment_bounds_to_bars(
    segments: list[dict],
    bar_starts: np.ndarray,
) -> list[dict]:
    """start/end каждого сегмента → ближайший bar_start."""
    out = []
    for s in segments:
        start = bar_starts[np.argmin(np.abs(bar_starts - s["start"]))]
        end = bar_starts[np.argmin(np.abs(bar_starts - s["end"]))]
        if end <= start:
            end = start + (60.0 / 120.0) * 4  # fallback 1 bar @ 120
        out.append({**s, "start": float(start), "end": float(end)})
    return out
```

**Правило резки MVP:** разрешённые точки реза = `bar_starts` ∩ `segment_boundaries` (объединение), плюс **intro/outro** (первый/последний сегмент) часто **protected**.

---

## 2. Алгоритм компоновки (поиск точек реза)

### 2.1. Входные данные

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Segment:
    id: int
    start: float          # сек
    end: float            # сек
    label: str
    protected: bool = False   # нельзя удалять (intro/hook/outro)
    weight: float = 1.0       # важность для cost

    @property
    def duration(self) -> float:
        return self.end - self.start
```

- `T_src = segments[-1].end` (или длина файла)
- `T_tgt` = Target_Time (сек)
- `Δ = T_src - T_tgt` — сколько **нужно вырезать** (если `Δ < 0` → только ускорение/loop не в MVP; отдельный режим)

Допуск: `ε = max(0.25, 0.005 * T_tgt)` сек (250 ms или 0.5%).

### 2.2. Дискретизация: кандидаты на удаление

Не режем произвольно середину сегмента. **Атом удаления** = один или несколько **смежных тактов** внутри непрерывного run сегментов, или **целый непротектed сегмент**.

```python
@dataclass
class RemovableBlock:
    """Непрерывный диапазон [start, end) который можно выкинуть."""
    start: float
    end: float
    segment_ids: tuple[int, ...]
    cost_remove: float  # меньше = приятнее резать

def build_removable_blocks(
    segments: list[Segment],
    bar_starts: np.ndarray,
    beats_per_bar: int = 4,
) -> list[RemovableBlock]:
    blocks = []
    for seg in segments:
        if seg.protected:
            continue
        bars_in = bar_starts[(bar_starts >= seg.start) & (bar_starts < seg.end)]
        if len(bars_in) < 2:
            continue
        # Блоки по 4/8 тактов (минимум 1 bar)
        bar_dur = np.median(np.diff(bar_starts)) if len(bar_starts) > 1 else 0.5
        chunk_bars = 4  # MVP: вырезаем куски по 4 такта
        for i in range(0, len(bars_in) - chunk_bars, chunk_bars):
            st, en = float(bars_in[i]), float(bars_in[i + chunk_bars])
            if en - st < 0.5:
                continue
            # cost: выше в середине припева — ниже cost (режем охотнее) — настраивается
            mid = (st + en) / 2
            centrality = 1.0 - abs(mid - (seg.start + seg.end) / 2) / (seg.duration / 2 + 1e-9)
            cost_remove = 0.3 * seg.weight + 0.7 * (1.0 - centrality)
            blocks.append(RemovableBlock(st, en, (seg.id,), cost_remove))
    return blocks
```

### 2.3. Математическая постановка

Пусть `blocks = {B_1..B_m}`, длительность `d_j = end_j - start_j`, стоимость удаления `c_j`.

Выбираем подмножество `S ⊆ {1..m}` такое что:

1. Блоки в `S` **не пересекаются** по времени (иначе двойной вырез).
2. После удаления остаётся **одна временная линия** (склейка left→right).
3. `|T_src - Σ_{j∈S} d_j - T_tgt| ≤ ε` — длина близка к цели.
4. Каждая склейка `(cut_out, cut_in)` на **bar boundary** (первая доля такта): `cut ≡ 0 (mod bar_period)` в beat grid.
5. Минимизируем `Σ_{j∈S} c_j` + штраф за отклонение длины.

Это **вариант subset sum / knapsack** с интервальными ограничениями. Точное решение — DP по **квантованной** длительности.

### 2.4. DP по длительности (точное совпадение ±ε)

Квантуем вырезание до **1 bar** (или 0.5 сек):

```python
def compose_dp(
    T_src: float,
    T_tgt: float,
    blocks: list[RemovableBlock],
    bar_quantum: float,
    epsilon: float,
) -> list[RemovableBlock] | None:
    need_remove = T_src - T_tgt
    if need_remove <= 0:
        return []

    Q = bar_quantum
    target_q = int(round(need_remove / Q))
    eps_q = int(math.ceil(epsilon / Q))

    # Сортируем блоки по start
    blocks = sorted(blocks, key=lambda b: b.start)
    m = len(blocks)

    # dp[i][r] = min cost to remove r quanta using first i blocks (non-overlap — упрощение: greedy+DP без overlap check)
    # Для MVP с non-overlap: сортировка + interval scheduling DP

    # Упрощённый 0/1 knapsack по суммарной длительности (игнор overlap — фильтруем заранее непересекающиеся)
    non_overlap = filter_non_overlapping_candidates(blocks)
    items = [(int(round((b.end - b.start) / Q)), b.cost_remove, b) for b in non_overlap]

    INF = 1e18
    max_r = target_q + eps_q + 5
    dp = [INF] * (max_r + 1)
    dp[0] = 0.0
    parent: list[tuple[int, RemovableBlock | None]] = [(0, None)] * (max_r + 1)

    for dur_q, cost, block in items:
        for r in range(max_r, dur_q - 1, -1):
            nc = dp[r - dur_q] + cost
            if nc < dp[r]:
                dp[r] = nc
                parent[r] = (r - dur_q, block)

    best_r, best_cost = None, INF
    for r in range(max(0, target_q - eps_q), target_q + eps_q + 1):
        if r < len(dp) and dp[r] < best_cost:
            best_cost, best_r = dp[r], r

    if best_r is None:
        return None

    # Восстановление
    chosen = []
    r = best_r
    while r > 0 and parent[r][1] is not None:
        prev_r, block = parent[r]
        if block is not None:
            chosen.append(block)
        r = prev_r
    return list(reversed(chosen))


def filter_non_overlapping_candidates(blocks: list[RemovableBlock]) -> list[RemovableBlock]:
    """Жадно оставляем длинные блоки с меньшим cost, без пересечений."""
    blocks = sorted(blocks, key=lambda b: (-(b.end - b.start), b.cost_remove))
    kept: list[RemovableBlock] = []
    for b in blocks:
        if all(b.end <= k.start or b.start >= k.end for k in kept):
            kept.append(b)
    return kept
```

**Фаза/доля:** если все `start/end` блоков — из `bar_starts`, склейка автоматически на **downbeat** при `phase_offset_beats=0`.

Для **3/4**: `beats_per_bar=3`, пересчитать `bar_starts`.

### 2.5. Альтернативы 3–5 вариантов

| # | Стратегия | Как получить |
|---|-----------|--------------|
| 1 | Минимальный cost (приоритет «неприметных» мест) | DP выше |
| 2 | Максимум сохранить intro+outro | `protected=True` на первом/последнем сегменте |
| 3 | Резать середину (максимум centrality cost на удаление) | инвертировать `cost_remove` |
| 4 | Меньше стыков | штраф `+λ * (#cuts)` в DP |
| 5 | Другой BPM-кандидат | повторить весь пайплайн со 2-м BPM из голосования |

```python
def generate_variants(
    segments: list[Segment],
    bar_starts: np.ndarray,
    T_tgt: float,
    n: int = 5,
) -> list[dict]:
    variants = []
    strategies = [
        {"name": "balanced", "cost_bias": 1.0, "lambda_cuts": 0.0},
        {"name": "keep_hooks", "cost_bias": 0.5, "lambda_cuts": 0.0, "protect_middle": True},
        {"name": "center_cut", "cost_bias": -1.0, "lambda_cuts": 0.0},
        {"name": "fewest_cuts", "cost_bias": 1.0, "lambda_cuts": 2.0},
    ]
    T_src = segments[-1].end
    for strat in strategies[:n]:
        blocks = build_removable_blocks(segments, bar_starts)
        if strat.get("cost_bias", 1) != 1.0:
            for b in blocks:
                b.cost_remove *= strat["cost_bias"]
        plan = compose_dp(T_src, T_tgt, blocks, bar_quantum=_median_bar_dur(bar_starts), epsilon=0.25)
        variants.append({"strategy": strat["name"], "removed": plan or []})
    return variants
```

### 2.6. План склейки → timeline

```python
@dataclass
class KeepRegion:
    start: float
    end: float

def build_keep_regions(
    T_src: float,
    removed: list[RemovableBlock],
) -> list[KeepRegion]:
    cuts = sorted(removed, key=lambda b: b.start)
    regions = []
    cursor = 0.0
    for b in cuts:
        if b.start > cursor:
            regions.append(KeepRegion(cursor, b.start))
        cursor = b.end
    if cursor < T_src:
        regions.append(KeepRegion(cursor, T_src))
    return regions
```

Итоговая длительность: `sum(r.end - r.start) - (n_crossfades * crossfade_overlap)`.

Подгонка под `T_tgt`: если после DP осталось `δ` сек — **trim** последнего keep region на bar boundary или изменить `chunk_bars` (2↔4).

---

## 3. Инженерия склейки и кроссфейдов (FFmpeg)

### 3.1. Почему FFmpeg, а не только PyDub

| Критерий | FFmpeg | PyDub |
|----------|--------|-------|
| Качество resample / dither | Отлично | Зависит от ffmpeg backend |
| Many cuts + crossfade chain | `filter_complex` | Медленнее, RAM |
| Продакшен | Стандарт | Прототип |

**MVP:** анализ в Librosa (22050 Hz mono), **рендер** в FFmpeg из **исходного файла** (48 kHz stereo), чтобы не терять качество.

### 3.2. Нарезка одного куска

```bash
ffmpeg -y -i input.wav -ss 12.340 -to 45.120 -c:a pcm_s16le part_00.wav
```

`-ss` после `-i` — точнее для склейки (медленнее). Для batch — один вызов с `filter_complex`.

### 3.3. Склейка списка регионов с acrossfade

```python
"""
render/ffmpeg_render.py
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Sequence

def render_timeline(
    input_path: Path,
    regions: Sequence[tuple[float, float]],
    output_path: Path,
    crossfade_sec: float = 0.04,
    sample_rate: int = 48000,
) -> None:
    """
    regions: [(start, end), ...] в секундах.
    crossfade_sec: 30–80 ms для ритмической музыки; 80–150 ms для амбиент/оркестр.
    """
    if not regions:
        raise ValueError("empty regions")
    n = len(regions)
    if n == 1:
        st, en = regions[0]
        cmd = [
            "ffmpeg", "-y", "-i", str(input_path),
            "-ss", f"{st:.6f}", "-to", f"{en:.6f}",
            "-ar", str(sample_rate), str(output_path),
        ]
        subprocess.run(cmd, check=True)
        return

    # [0:a]atrim=...,asetpts; ... → acrossfade chain
    parts = []
    for i, (st, en) in enumerate(regions):
        parts.append(
            f"[0:a]atrim=start={st:.6f}:end={en:.6f},asetpts=PTS-STARTPTS[a{i}]"
        )
    stream_labels = "".join(f"[a{i}]" for i in range(n))
    # Цепочка acrossfade: [a0][a1]acrossfade=...[af1]; [af1][a2]acrossfade...
    fade = f"acrossfade=d={crossfade_sec:.4f}:c1=qsin:c2=qsin:overlap=1"
    if n == 2:
        chain = f"{parts[0]};{parts[1]};[a0][a1]{fade}[out]"
    else:
        # Пошаговая цепочка
        lines = [parts[0] + ";", parts[1] + ";", f"[a0][a1]{fade}[x1];"]
        for i in range(2, n):
            lines.append(parts[i] + ";")
            prev = f"x{i-1}"
            cur = f"x{i}" if i < n - 1 else "out"
            lines.append(f"[{prev}][a{i}]{fade}[{cur}];")
        chain = "".join(lines).rstrip(";")
    filter_complex = chain

    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-ar", str(sample_rate),
        str(output_path),
    ]
    subprocess.run(cmd, check=True)
```

**Эквивалент CLI (2 фрагмента):**

```bash
ffmpeg -i full.wav -filter_complex \
"[0:a]atrim=start=0:end=30,asetpts=PTS-STARTPTS[a0]; \
 [0:a]atrim=start=60:end=90,asetpts=PTS-STARTPTS[a1]; \
 [a0][a1]acrossfade=d=0.04:c1=qsin:c2=qsin:overlap=1[out]" \
-map "[out]" output.wav
```

### 3.4. Параметры «идеального» кроссфейда (без щелчков и провалов)

| Параметр | Рекомендация | Почему |
|----------|--------------|--------|
| `d` (duration) | **1–2 периода** при 48 kHz: `d = 2 * sr / f_low` ≈ 40–80 ms; старт **40 ms** | Короче → click; длиннее → двойной удар |
| `c1`, `c2` | **`qsin`** или **`exp`** симметрично | `tri` даёт провал −3 dB в центре |
| `overlap=1` | Да (по умолчанию) | Плавное наложение |
| Выравнивание громкости | `loudnorm` или RMS match перед fade | Избегает скачка LUFS на стыке |
| Фаза | Резать на **zero-crossing** / onset (§1.2.D) | Снижает phase cancellation |

**Провал громкости:** при equal-power crossfade используйте кривые, дающие `sin² + cos² = 1`. FFmpeg `qsin` близок к equal-power.

```python
def match_rms_before_concat(wav_paths: list[Path], target_rms_db: float = -18.0) -> None:
    """Опционально: pydub или ffmpeg loudnorm на каждом куске."""
    pass
```

**Щелчки:** применить `afade=t=in:st=0:d=0.005` на каждом куске (5 ms fade-in) **вне** зоны acrossfade.

### 3.5. pydub (быстрый прототип)

```python
from pydub import AudioSegment

def pydub_concat(regions_ms: list[tuple[int, int]], path: str, crossfade_ms: int = 40) -> AudioSegment:
    audio = AudioSegment.from_file(path)
    out = AudioSegment.empty()
    for i, (st, en) in enumerate(regions_ms):
        chunk = audio[st:en]
        if i == 0:
            out = chunk
        else:
            out = out.append(chunk, crossfade=crossfade_ms)
    return out
```

---

## 4. Архитектура API (FastAPI) и производительность

### 4.1. Почему не BackgroundTasks для тяжёлого CPU

`BackgroundTasks` выполняется **в том же процессе** после ответа — при 2–3 параллельных треках 5 мин WAV сервер **захлебнётся** (GIL + RAM).

| Режим | Когда |
|-------|-------|
| **Celery + Redis** | Прод, несколько воркеров, очередь, retry |
| **RQ / ARQ** | Проще Celery, один Redis |
| **Отдельный worker process + SQLite/Redis queue** | MVP без брокера |
| BackgroundTasks | Только <10 с задачи (превью 30 с) |

### 4.2. Скелет API

```python
"""
app/main.py — скелет FastAPI для audio composition MVP.
"""
from __future__ import annotations

import uuid
from enum import Enum
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

app = FastAPI(title="Audio Compose MVP", version="0.1.0")

UPLOAD_DIR = Path("/data/uploads")
OUTPUT_DIR = Path("/data/outputs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class JobStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    done = "done"
    failed = "failed"


class JobCreateResponse(BaseModel):
    job_id: str
    status: JobStatus


class JobDetail(BaseModel):
    job_id: str
    status: JobStatus
    target_sec: float
    progress: float = 0.0
    error: str | None = None
    variants: list[dict] | None = None  # URLs или метаданные 3–5 вариантов


# MVP in-memory; прод: Redis/Postgres
JOBS: dict[str, JobDetail] = {}


@app.post("/v1/compose", response_model=JobCreateResponse, status_code=202)
async def create_compose_job(
    file: UploadFile = File(...),
    target_sec: float = Form(..., gt=0.5, le=600),
    beats_per_bar: int = Form(4),
    n_variants: int = Form(3, ge=1, le=5),
):
    if file.content_type and not file.content_type.startswith("audio/"):
        raise HTTPException(400, "Expected audio file")
    job_id = str(uuid.uuid4())
    dest = UPLOAD_DIR / f"{job_id}_{file.filename}"
    content = await file.read()
    if len(content) > 80 * 1024 * 1024:
        raise HTTPException(413, "Max 80 MB in MVP")
    dest.write_bytes(content)

    JOBS[job_id] = JobDetail(
        job_id=job_id, status=JobStatus.queued, target_sec=target_sec
    )
    # Прод: celery_app.send_task("tasks.compose", args=[job_id, str(dest), target_sec, ...])
    enqueue_compose(job_id, dest, target_sec, beats_per_bar, n_variants)
    return JobCreateResponse(job_id=job_id, status=JobStatus.queued)


@app.get("/v1/jobs/{job_id}", response_model=JobDetail)
async def get_job(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


def enqueue_compose(job_id: str, path: Path, target_sec: float, bpb: int, n_variants: int) -> None:
    """MVP: thread pool / subprocess. Прод: Celery."""
    import threading
    threading.Thread(
        target=_run_compose_worker,
        args=(job_id, path, target_sec, bpb, n_variants),
        daemon=True,
    ).start()


def _run_compose_worker(job_id: str, path: Path, target_sec: float, bpb: int, n_variants: int) -> None:
    job = JOBS[job_id]
    try:
        job.status = JobStatus.processing
        # 1) analyze 2) compose 3) render variants
        # from pipeline import run_full_pipeline
        # job.variants = run_full_pipeline(path, target_sec, bpb, n_variants)
        job.progress = 1.0
        job.status = JobStatus.done
    except Exception as e:
        job.status = JobStatus.failed
        job.error = str(e)
```

### 4.3. Celery task (прод)

```python
# tasks/compose.py
from celery import Celery

celery_app = Celery("compose", broker="redis://localhost:6379/0")

@celery_app.task(bind=True, max_retries=2, time_limit=600)
def compose_task(self, job_id: str, input_path: str, target_sec: float, opts: dict):
    self.update_state(state="PROGRESS", meta={"pct": 0.1})
    # analyze → compose → ffmpeg
    self.update_state(state="PROGRESS", meta={"pct": 0.7})
    # upload to S3 / write OUTPUT_DIR
    return {"variants": [...]}
```

**Ограничение параллелизма:** `worker_prefetch_multiplier=1`, `concurrency=2` на 4-core CPU.

### 4.4. Контракт для JS-фронта

```
POST /v1/compose → 202 { job_id }
GET  /v1/jobs/{id} → polling каждые 1–2 с
GET  /v1/jobs/{id}/download/{variant_index} → 302 на файл
```

**Rate limit:** 5 активных jobs / user; max duration 10 min source.

### 4.5. Производительность и RAM

| Этап | Оценка 4 min WAV | Оптимизация |
|------|------------------|-------------|
| librosa load 22050 | ~2–5 s | один канал, фикс. sr |
| beat + segments | ~5–15 s | кэш envelope |
| DP | <1 s | квант bar |
| ffmpeg | ~3–10 s | один filter_complex |

Пик RAM: **не держать** полный decode stereo 48kHz в numpy; FFmpeg читает файл с диска.

---

## 5. Чек-лист для заказчика

Ответы **Да/Нет** жёстко фиксируют MVP. Попросите отметить до старта разработки.

| # | Вопрос | Да = в scope MVP | Нет = out of scope |
|---|--------|------------------|---------------------|
| 1 | Исходники **только** инструментал/электроника с устойчивым ритмом (без вокала как основного слоя)? | | |
| 2 | Максимальная длина исходника **≤ 6 минут**, размер файла **≤ 80 MB**? | | |
| 3 | Форматы на вход: **WAV/MP3/FLAC**; на выход — **один** формат (WAV **или** MP3)? | | |
| 4 | Целевое время задаётся **одним числом** (сек), допуск **±0.25 с** — приемлемо? | | |
| 5 | Допустимо **сокращение** (3:40 → 1:30); **удлинение** трека не нужно в MVP? | | |
| 6 | Размер такта фиксирован: **4/4** (или отдельно оговорён **3/4**), без смены размера внутри трека? | | |
| 7 | Достаточно **3–5 вариантов** склейки на одно `Target_Time`, без ручного редактора в браузере? | | |
| 8 | Intro/outro **не режем** (первые/последние N тактов protected)? | | |
| 9 | Обработка **асинхронная** (очередь 1–5 мин), без «мгновенного» ответа в HTTP? | | |
| 10 | Хостинг: **один** CPU-сервер (2–4 workers), без SLA «студийного» качества для джаза/оркестра/live? | | |

**Если хотя бы на #1, #6 или #10 ответ «Нет»** — заложите отдельную фазу / доп. бюджет или явный disclaimer в договоре.

---

## 6. Рекомендуемая структура репозитория MVP

```
audio-compose-mvp/
├── app/
│   ├── main.py              # FastAPI
│   ├── models.py
│   └── storage.py
├── analysis/
│   ├── beats.py
│   ├── segments.py
│   └── pipeline.py          # analyze() → beats, segments, blocks
├── compose/
│   ├── blocks.py
│   ├── dp.py
│   └── variants.py
├── render/
│   └── ffmpeg_render.py
├── tasks/
│   └── compose_celery.py    # опционально
├── tests/
│   ├── test_beats.py
│   └── test_dp.py
├── requirements.txt
└── docker-compose.yml       # api + redis + worker
```

**requirements.txt (минимум):**

```
fastapi>=0.110
uvicorn[standard]>=0.27
python-multipart
librosa>=0.10.2
numpy>=1.26
scipy>=1.11
soundfile>=0.12
celery>=5.3
redis>=5.0
# ffmpeg в PATH системы
```

---

## Приложение A: End-to-end orchestration

```python
def run_full_pipeline(
    input_path: Path,
    target_sec: float,
    beats_per_bar: int = 4,
    n_variants: int = 3,
) -> list[dict]:
    y, sr = load_mono(str(input_path))
    onset_env = onset_envelope(y, sr)
    bpm, beat_times = pick_best_bpm(y, sr, onset_env)
    if _ioi_cv(beat_times) > 0.12:
        _, beat_times = beats_with_dynamic_tempo(y, sr)
    beat_times = filter_beats_by_ioi(beat_times, bpm)
    _, bar_starts = quantize_to_bars(beat_times, bpm, beats_per_bar)

    segments = structural_segments_foote(y, sr)
    segments = snap_segment_bounds_to_bars(segments, bar_starts)
    if segments:
        segments[0]["protected"] = True
        segments[-1]["protected"] = True

    seg_objs = [
        Segment(i, s["start"], s["end"], s.get("label", f"S{i}"), s.get("protected", False))
        for i, s in enumerate(segments)
    ]
    T_src = seg_objs[-1].end
    variants_meta = generate_variants(seg_objs, bar_starts, target_sec, n=n_variants)

    results = []
    for v in variants_meta:
        regions = build_keep_regions(T_src, v["removed"])
        out = input_path.parent / f"{input_path.stem}_{v['strategy']}.wav"
        render_timeline(input_path, [(r.start, r.end) for r in regions], out)
        results.append({"strategy": v["strategy"], "path": str(out)})
    return results
```

---

## Приложение B: Риски и ожидания (для договора)

| Риск | Митигация |
|------|-----------|
| Двойной удар на стыке | bar-aligned cuts + 40 ms qsin crossfade |
| «Плывущий» BPM | dynamic tempo / PLP + disclaimer |
| Вокал ведёт onset | отдельный канал/HPSS (librosa.effects.hpss) — **фаза 2** |
| Клиент ждёт TuneBlades 1:1 | ссылка на seam-carving DP (Disney) как v2, не MVP |

---

## Ссылки

- [librosa.beat.beat_track](https://librosa.org/doc/main/generated/librosa.beat.beat_track.html)
- [Dynamic beat tracking example](https://librosa.org/doc/main/auto_examples/plot_dynamic_beat.html)
- [Laplacian segmentation example](https://librosa.org/doc/main/auto_examples/plot_segmentation.html)
- [Foote novelty / checkerboard (FMP)](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C4/C4S4_NoveltySegmentation.html)
- [FFmpeg acrossfade](https://ayosec.github.io/ffmpeg-filters-docs/7.0/Filters/Audio/acrossfade.html)
- Ellis (2007) — Beat Tracking by Dynamic Programming
- Wenner et al. (2013) — Scalable Music: Automatic Music Retargeting and Synthesis

---

_Документ для реализации в отдельном сервисе; не входит в канон RawLead (`docs/team/common/DOCS_ARCHITECTURE.md`)._
