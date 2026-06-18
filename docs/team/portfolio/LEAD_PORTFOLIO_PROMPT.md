# Lead Portfolio — активный план



**Owner:** 2026-06-18 · **mood с нуля** · Claude Code = руки · `@lead-portfolio` = идеи + промпты.



---



## → Now: P2 — polish pass (desktop 1440)



**P1 v1 desktop — owner sign-off 2026-06-18.** Секции собраны · `npm run build` ✅ static export.



| # | Deliverable | Кто | Статус |

|---|-------------|-----|--------|

| p1 Hero + scramble physics | Claude Code | ✅ |

| p1 Tagline typewriter | Claude Code | ✅ |

| p1 Services (4 карточки) | Claude Code | ✅ |

| p1 Projects / RawLead (4 кейса + terminal) | Claude Code | ✅ |

| p1 Process (3 шага) | Claude Code | ✅ |

| p1 Footer CTA | Claude Code | ✅ |

| p1 SEO metadata | Claude Code | ✅ |

| p2 **Polish pass** — единый ритм, motion, cleanup | Claude Code | ⏳ |

| p2 Удалить мёртвый код + `.tmp.*` | Claude Code | ⏳ |

| p3 Mobile 390px | отложено | ⏸ |

| p4 Deploy **rode51.ru** (было labs.rawlead.ru) | owner DNS + @coder nginx/BASE_URL | ⏳ owner: Beget DNS → [`RODE51_BEGET_DNS.md`](../../ops/RODE51_BEGET_DNS.md) |



**Промпт polish:** `CLAUDE_CODE_HANDOFF.md` § `polish-v1`.



---



## Приёмка P1 (Lead Portfolio, 2026-06-18)



### Desktop 1440 — **PASS**



| Критерий | Вердикт |

|----------|---------|

| Премиально, не шаблон | ✅ |

| Понятно «dev / автоматизация / prod» | ✅ |

| CTA @rcnn43 виден (Hero + Footer) | ✅ |

| RawLead = один проект, 4 главы | ✅ |

| Без цены / Stars в кейсе | ✅ |

| Терминал — публичный словарь | ✅ (FL/Kwork в логе кейса — ок) |

| Static build | ✅ `next build` |



### Замечания (не блокер P1, в polish)



- Зелёный badge «ДОСТУПЕН» — второй акцент кроме amber (можно оставить или унифицировать)

- `Cases.tsx`, `CaseSection.tsx`, `ProductResult.tsx` — не в `page.tsx`, удалить

- `*.tmp.*` в `app/components/` — удалить

- `prefers-reduced-motion` — не везде

- Mobile — **не трогаем** до P3 (owner)



---



## Структура страницы (as-built)



```

Hero          — RODE51 scramble + typewriter + badge + ticker

Tagline       — «Больше делаю, меньше обещаю.»

Services      — БОТ / ПАРСЕР / АВТОМАТИЗАЦИЯ / ИНТЕГРАЦИЯ

Projects      — RAWLEAD accordion → 4 кейса rail + TerminalLog в ПАРСЕР

Process       — 3 шага для FL-клиента

Footer        — «Есть задача?» + @rcnn43

```



Hero copy (as-built): `РАЗРАБОТКА · АВТОМАТИЗАЦИЯ · ИНТЕГРАЦИИ` + две строки value prop.



---



## Mood § (approved)



Rode51 — инженер с живым prod. Тёмный editorial + terminal. Amber `#F5A623` — основной акцент. Barlow Condensed 900 + Geist Mono. Desktop 1440 first.



**Anti-patterns:** purple slop · Visio-диаграммы · выдуманные метрики · копия NEO rawlead.ru UI.



---



## Архив решений



| Дата | Решение |

|------|---------|

| 2026-06-18 | Mood с нуля · P288 ❌ · `@lead-portfolio` |

| 2026-06-18 | Desktop-first · mobile polish отложен |

| 2026-06-18 | RawLead = 4 кейса внутри одного проекта (не 4 фейковых продукта) |

| 2026-06-18 | **P1 v1 desktop принят** → P2 polish |



_Старые § — `docs/team/archive/` при переносе Lead Architect._

