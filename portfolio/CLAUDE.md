# Rode51 Portfolio — Claude Code Context

**Target:** labs.rawlead.ru · Static Next.js export · Owner decision: 2026-06-18

## Primary canvas

**Desktop 1440–1920px is primary.** Mobile 390px = sanity gate, не блокирует desktop v1.

## Approved design system

| Token | Value | Rule |
|-------|-------|------|
| bg | `#0e0e0e` | Always dark |
| surface | `#141414` | Cards |
| text | `#e8e8e8` | Body |
| muted | `#555555` | Meta/labels |
| edge | `#222222` | Borders |
| amber | `#F5A623` | ONLY accent — CTA, одна метрика, hover |
| display | Barlow Condensed 900 | Hero + section headers |
| mono | Geist Mono | Всё остальное — meta, labels, terminal |

**Amber — максимум 4 места на странице. На hero title НИКОГДА (только snow).**

## Build order

Hero ✅ → Tagline ✅ → Services ✅ → Projects ✅ → Process ✅ → Footer ✅ → **P2 polish**

## As-built page map

| Section | Component | Notes |
|---------|-----------|-------|
| Hero | `Hero.tsx` + `ScrambleTitle.tsx` + `Ticker.tsx` | scramble physics, typewriter, availability badge |
| Tagline | `Tagline.tsx` | «Больше делаю, меньше обещаю.» |
| Services | `Services.tsx` | 4 cards, minimal SVG icons |
| Projects | `Projects.tsx` + `TerminalLog.tsx` | RAWLEAD accordion, 4 cases, metrics inline |
| Process | `Process.tsx` | 3 steps FL workflow |
| Footer | `Footer.tsx` | CTA @rcnn43 |
| Global | `CustomCursor`, `Grain`, `SmoothScroll`, `ScrollUI` | layout.tsx |

**Dead code (delete in polish):** `Cases.tsx`, `CaseSection.tsx`, `ProductResult.tsx`, `CursorGlow.tsx`, `*.tmp.*`

## P2 polish goals

- Unify section spacing (py/gap rhythm)
- Audit amber usage (max 4–5 accents page-wide)
- prefers-reduced-motion on scramble, typewriter, ticker
- Remove dead files
- web-design-guidelines pass on all components
- **Do NOT redesign structure** — polish only unless owner asks

## Hard constraints

- НЕ копировать rawlead.ru NEO UI (Manrope, жёлтый, hard borders).
- Нет WebGL / Three.js в v1.
- Нет mp4 autoplay — только CSS ambient.
- Нет цены, Stars, продажного текста в кейсах.
- Публичный словарь: radar, L1/L2/L3, lenta, cabinet, TG notify. НЕ @FLPARSINGBOT и внутренние имена.
- Личный бренд (подзаголовок) утверждён: **"Больше делаю, меньше обещаю."**

## Stack

Next.js 14 App Router · TypeScript · Tailwind CSS · `output: "export"` (полностью статика)
Framer Motion — для v1.1+ переходов, пока не использовать.

## Физика букв — параметры (ScrambleTitle)

```
CURSOR_RADIUS   = 190
CURSOR_STRENGTH = 5.8
SPRING          = 0.038
DAMPING         = 0.88
COL_ITERS       = 8
Y_SCALE         = 0.40
```
Verlet integration + position-based collision. Менять осторожно.
