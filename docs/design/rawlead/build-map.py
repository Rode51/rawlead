# -*- coding: utf-8 -*-
"""One-off: build project-map-owner.svg + .png (UTF-8 safe on Windows)."""
from pathlib import Path

DIR = Path(__file__).resolve().parent
SVG = DIR / "project-map-owner.svg"
PNG = DIR / "project-map-owner.png"

svg = r'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">
  <defs>
    <style>
      @font-face {
        font-family: 'Manrope';
        src: url('Manrope-Variable.ttf') format('truetype');
        font-weight: 100 800;
      }
      .title { font-family: Manrope, sans-serif; font-size: 32px; font-weight: 800; fill: #eceef4; }
      .title-accent { fill: #5b8def; }
      .subtitle { font-family: Manrope, sans-serif; font-size: 15px; font-weight: 500; fill: #8b93a7; }
      .section { font-family: Manrope, sans-serif; font-size: 11px; font-weight: 700; letter-spacing: 1.2px; fill: #8b93a7; text-transform: uppercase; }
      .node-title { font-family: Manrope, sans-serif; font-size: 15px; font-weight: 700; fill: #eceef4; }
      .node-sub { font-family: Manrope, sans-serif; font-size: 12px; font-weight: 500; fill: #8b93a7; }
      .small { font-family: Manrope, sans-serif; font-size: 12px; font-weight: 600; fill: #8b93a7; }
      .rule { font-family: Manrope, sans-serif; font-size: 13px; font-weight: 600; fill: #ef9a9a; }
      .role-title { font-family: Manrope, sans-serif; font-size: 14px; font-weight: 800; fill: #eceef4; }
      .role-sub { font-family: Manrope, sans-serif; font-size: 11px; font-weight: 600; fill: #8b93a7; }
      .role-body { font-family: Manrope, sans-serif; font-size: 12px; font-weight: 500; fill: #8b93a7; }
      .tag { font-family: Manrope, sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 0.4px; fill: #8b93a7; text-transform: uppercase; }
      .footer { font-family: Manrope, sans-serif; font-size: 12px; font-weight: 500; fill: #5c6370; }
      .badge { font-family: Manrope, sans-serif; font-size: 13px; font-weight: 600; fill: #8b93a7; }
      .acc { font-family: Manrope, sans-serif; font-size: 12px; font-weight: 700; fill: #eceef4; }
      .acc-sub { font-family: Manrope, sans-serif; font-size: 10px; font-weight: 500; fill: #8b93a7; }
      .source { font-family: Manrope, sans-serif; font-size: 12px; font-weight: 600; fill: #b8c9ef; }
    </style>
    <linearGradient id="bgGlow" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#5b8def" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="#0c0e13" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="pultGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#5b8def" stop-opacity="0.12"/>
      <stop offset="100%" stop-color="#0c0e13" stop-opacity="1"/>
    </linearGradient>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 Z" fill="#5c6370"/>
    </marker>
    <marker id="arrBlue" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 Z" fill="#5b8def"/>
    </marker>
    <marker id="arrGreen" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 Z" fill="#3dd68c"/>
    </marker>
    <filter id="glowGreen" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="8" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>

  <rect width="1920" height="1080" fill="#0c0e13"/>
  <ellipse cx="960" cy="0" rx="900" ry="500" fill="url(#bgGlow)"/>
  <ellipse cx="1700" cy="1050" rx="600" ry="400" fill="#3dd68c" opacity="0.04"/>

  <line x1="56" y1="118" x2="1864" y2="118" stroke="#2a3140"/>
  <text x="56" y="72" class="title"><tspan class="title-accent">RAWLEAD</tspan> — как устроен радар на твоём ПК</text>
  <text x="56" y="98" class="subtitle">Одна страница · без кода · по PROJECT_MAP</text>

  <rect x="1580" y="44" width="284" height="34" rx="17" fill="#141820" stroke="#2a3140"/>
  <circle cx="1604" cy="61" r="4" fill="#3dd68c"/>
  <circle cx="1604" cy="61" r="8" fill="#3dd68c" opacity="0.25"/>
  <text x="1620" y="66" class="badge">max 2 python-процесса</text>

  <rect x="56" y="140" width="1808" height="620" rx="20" fill="#141820" stroke="#2a3140"/>
  <text x="88" y="176" class="section">1 · программы на компьютере</text>

  <g fill="none" stroke-width="1.5">
    <path d="M 230 250 H 360" stroke="#5b8def" marker-end="url(#arrBlue)"/>
    <path d="M 500 250 H 760" stroke="#5c6370" marker-end="url(#arr)"/>
    <path d="M 460 250 C 460 210, 1540 210, 1540 250" stroke="#5c6370" marker-end="url(#arr)"/>
    <path d="M 940 250 H 1420" stroke="#5b8def" marker-end="url(#arrBlue)"/>
    <path d="M 1480 290 C 1480 430, 420 430, 420 500" stroke="#3dd68c" marker-end="url(#arrGreen)"/>
    <path d="M 1520 290 C 1520 430, 1030 430, 1030 500" stroke="#3dd68c" marker-end="url(#arrGreen)"/>
    <path d="M 500 580 C 500 620, 860 620, 860 650" stroke="#5c6370" marker-end="url(#arr)"/>
    <path d="M 1030 580 C 1030 620, 920 620, 920 650" stroke="#5c6370" marker-end="url(#arr)"/>
    <path d="M 480 540 C 580 540, 1300 600, 1540 650" stroke="#5b8def" marker-end="url(#arrBlue)"/>
    <path d="M 1070 540 C 1170 580, 1400 620, 1540 650" stroke="#5b8def" marker-end="url(#arrBlue)"/>
    <path d="M 1640 680 C 1700 680, 1700 220, 160 220, 160 250" stroke="#5b8def" marker-end="url(#arrBlue)"/>
  </g>

  <rect x="88" y="210" width="142" height="80" rx="14" fill="#0c0e13" stroke="#5b8def"/>
  <text x="159" y="244" text-anchor="middle" class="node-title">Ты</text>
  <text x="159" y="266" text-anchor="middle" class="node-sub">владелец · .env</text>

  <rect x="360" y="210" width="140" height="80" rx="14" fill="#0c0e13" stroke="#2a3140"/>
  <text x="430" y="244" text-anchor="middle" class="node-title">Ярлык VBS</text>
  <text x="430" y="266" text-anchor="middle" class="node-sub">start-radar-desktop</text>

  <rect x="760" y="200" width="180" height="100" rx="14" fill="url(#pultGrad)" stroke="#5b8def"/>
  <text x="850" y="240" text-anchor="middle" class="node-title">Пульт RawLead</text>
  <text x="850" y="262" text-anchor="middle" class="node-sub">Tauri · ▶ ■ ✕</text>

  <rect x="1420" y="210" width="180" height="80" rx="14" fill="#090b10" stroke="#3a4255"/>
  <text x="1510" y="244" text-anchor="middle" class="node-title">radar_control</text>
  <text x="1510" y="266" text-anchor="middle" class="node-sub">127.0.0.1:18765 · .venv</text>

  <text x="850" y="322" text-anchor="middle" class="small">управление с пульта</text>

  <rect x="640" y="340" width="420" height="44" rx="12" fill="rgba(239,107,107,0.08)" stroke="rgba(239,107,107,0.35)"/>
  <text x="850" y="367" text-anchor="middle" class="rule">Не больше 2 процессов: main.py + tg_main.py · только .venv</text>

  <rect x="200" y="510" width="100" height="32" rx="10" fill="rgba(91,141,239,0.06)" stroke="rgba(91,141,239,0.2)"/>
  <text x="250" y="531" text-anchor="middle" class="source">FL.ru</text>
  <rect x="200" y="548" width="100" height="32" rx="10" fill="rgba(91,141,239,0.06)" stroke="rgba(91,141,239,0.2)"/>
  <text x="250" y="569" text-anchor="middle" class="source">Kwork</text>
  <path d="M 300 526 H 340" stroke="#5c6370" stroke-width="1.2" fill="none" marker-end="url(#arr)"/>
  <path d="M 300 564 H 340" stroke="#5c6370" stroke-width="1.2" fill="none" marker-end="url(#arr)"/>

  <rect x="340" y="500" width="160" height="80" rx="14" fill="#0c0e13" stroke="#3dd68c" filter="url(#glowGreen)"/>
  <text x="420" y="536" text-anchor="middle" class="node-title">main.py</text>
  <text x="420" y="558" text-anchor="middle" class="node-sub">биржи · парсеры</text>

  <rect x="940" y="500" width="180" height="80" rx="14" fill="#0c0e13" stroke="#3dd68c" filter="url(#glowGreen)"/>
  <text x="1030" y="536" text-anchor="middle" class="node-title">tg_main.py</text>
  <text x="1030" y="558" text-anchor="middle" class="node-sub">Telethon · join внутри</text>

  <rect x="900" y="600" width="72" height="52" rx="10" fill="#0c0e13" stroke="#2a3140"/>
  <text x="936" y="624" text-anchor="middle" class="acc">acc1</text>
  <text x="936" y="640" text-anchor="middle" class="acc-sub">чаты TG</text>
  <rect x="984" y="600" width="72" height="52" rx="10" fill="#0c0e13" stroke="#2a3140"/>
  <text x="1020" y="624" text-anchor="middle" class="acc">acc2</text>
  <text x="1020" y="640" text-anchor="middle" class="acc-sub">чаты TG</text>
  <rect x="1068" y="600" width="72" height="52" rx="10" fill="#0c0e13" stroke="#2a3140"/>
  <text x="1104" y="624" text-anchor="middle" class="acc">acc3</text>
  <text x="1104" y="640" text-anchor="middle" class="acc-sub">чаты TG</text>

  <rect x="780" y="660" width="160" height="72" rx="14" fill="rgba(9,11,16,0.8)" stroke="#3a4255" stroke-dasharray="6 4"/>
  <text x="860" y="694" text-anchor="middle" class="node-title">data/</text>
  <text x="860" y="716" text-anchor="middle" class="node-sub">БД · логи · сессии</text>

  <rect x="1480" y="660" width="180" height="72" rx="14" fill="#0c0e13" stroke="#5b8def"/>
  <text x="1570" y="694" text-anchor="middle" class="node-title">Telegram-бот</text>
  <text x="1570" y="716" text-anchor="middle" class="node-sub">уведомления тебе</text>

  <rect x="56" y="784" width="1808" height="220" rx="20" fill="#141820" stroke="#2a3140"/>
  <text x="88" y="820" class="section">2 · кто что трогает (роли cursor)</text>

  <rect x="88" y="844" width="200" height="132" rx="14" fill="#0c0e13" stroke="#5b8def"/>
  <text x="108" y="874" class="role-title">Ты</text>
  <text x="108" y="904" class="role-body">Запуск, .env, бэкап</text>
  <text x="108" y="922" class="role-body">data/, FOR_YOU.md</text>
  <rect x="108" y="940" width="110" height="22" rx="6" fill="rgba(255,255,255,0.04)"/>
  <text x="116" y="955" class="tag">задача → lead</text>

  <rect x="312" y="844" width="420" height="132" rx="14" fill="#0c0e13" stroke="#8b93a7"/>
  <text x="332" y="874" class="role-title">Lead</text>
  <text x="392" y="874" class="role-sub">@lead-architect</text>
  <text x="332" y="904" class="role-body">docs/team/* · CODER_PROMPT · PROJECT_MAP</text>
  <text x="332" y="922" class="role-body">без кода</text>
  <rect x="332" y="940" width="130" height="22" rx="6" fill="rgba(91,141,239,0.08)"/>
  <text x="340" y="955" class="tag" fill="#5b8def">промпт → coder</text>

  <rect x="756" y="844" width="520" height="132" rx="14" fill="#0c0e13" stroke="#3dd68c"/>
  <text x="776" y="874" class="role-title">Coder</text>
  <text x="842" y="874" class="role-sub">@coder</text>
  <text x="776" y="904" class="role-body">src/ · scripts/ · desktop/</text>
  <text x="776" y="922" class="role-body">только файлы из промпта</text>
  <rect x="776" y="940" width="130" height="22" rx="6" fill="rgba(61,214,140,0.08)"/>
  <text x="784" y="955" class="tag" fill="#3dd68c">status → lead</text>

  <rect x="1300" y="844" width="520" height="132" rx="14" fill="#0c0e13" stroke="#ef6b6b"/>
  <text x="1320" y="874" class="role-title">Mechanic</text>
  <text x="1418" y="874" class="role-sub">@mechanic</text>
  <text x="1320" y="904" class="role-body">Чинит по тикету docs/problems/</text>
  <text x="1320" y="922" class="role-body">закрывает тикет → Lead</text>
  <rect x="1320" y="940" width="110" height="22" rx="6" fill="rgba(239,107,107,0.08)"/>
  <text x="1328" y="955" class="tag" fill="#ef6b6b">тикет ← lead</text>

  <path d="M 288 910 H 312" stroke="#5c6370" stroke-width="1.5" fill="none" marker-end="url(#arr)"/>
  <path d="M 732 910 H 756" stroke="#5c6370" stroke-width="1.5" fill="none" marker-end="url(#arr)"/>
  <path d="M 1276 910 H 1300" stroke="#5c6370" stroke-width="1.5" fill="none" marker-end="url(#arr)"/>

  <text x="1864" y="1060" text-anchor="end" class="footer">docs/design/rawlead · Manrope · палитра пульта #0c0e13 · 2026-05-24</text>
</svg>
'''

SVG.write_text(svg, encoding="utf-8")
print("Wrote", SVG)
