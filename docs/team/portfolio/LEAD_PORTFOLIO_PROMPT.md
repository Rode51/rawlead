# Lead Portfolio — активный план



**Owner:** 2026-06-18 · **mood с нуля** · Claude Code = руки · `@lead-portfolio` = идеи + промпты.



---



## → Now: P2 — polish + контент (desktop 1440)



**P1 v1 desktop — owner sign-off 2026-06-18.** **Prod:** https://rode51.ru — P1 live (Lead verify fetch 2026-06-20).



| # | Deliverable | Кто | Статус |

|---|-------------|-----|--------|

| p1 Hero + scramble physics | Claude Code | ✅ prod |

| p1 Tagline typewriter | Claude Code | ✅ prod |

| p1 Services (4 карточки) | Claude Code | ✅ prod → **6** в WIP |

| p1 Projects / RawLead (4 кейса + terminal) | Claude Code | ✅ prod |

| p1 Process (3 шага) | Claude Code | ✅ prod |

| p1 Footer CTA | Claude Code | ✅ prod |

| p1 SEO metadata | Claude Code | ✅ prod (⚠️ `metadataBase` ещё `rawlead.ru/portfolio` — fix в WIP) |

| **p2 WhyMe** (`/ ПОЧЕМУ Я`, 4 карточки) | Claude Code | ✅ локально · **не на prod** |

| **p2 FAQ** (accordion 4 вопроса) | Claude Code | ✅ локально · **не на prod** |

| **p2 EN** `/en` + `lib/content/{ru,en}.ts` | Claude Code | ✅ `npm run build` 6 static pages · **не на prod** |

| p2 Polish Hero/Footer/Services/Projects | Claude Code | ⏳ WIP uncommitted |

| p2 Удалить мёртвый код + `.tmp.*` | Claude Code | ⏳ `Cases.tsx`, `CaseSection.tsx`, … ещё в repo |

| p3 Mobile 390px | отложено | ⏸ |

| p4 Deploy **rode51.ru** | owner «задеплой» + @lead-architect | ✅ P1 · **повторный deploy** после P2 merge |



**Lead verify 2026-06-20:** `portfolio/` build ✅ (`/` + `/en` static). Prod HTML — без WhyMe/FAQ (старая сборка). Diff ~13 файлов + `lib/content/` — **не в git**, не на VPS.



**До deploy P2:** поправить `layout.tsx` → `metadataBase: https://rode51.ru` · owner desktop 1440 скрин · `@lead-architect` → `deploy-portfolio-rode51-vps.py`.



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
Services      — 6 карточек (WIP: +ЛЕНДИНГ, +САЙТ)
WhyMe         — 4 причины (fixed price, оплата после, remote, поддержка)  [P2 WIP]
Projects      — RAWLEAD accordion → 4 кейса rail + TerminalLog
Process       — 3 шага для FL-клиента
FAQ           — 4 вопроса accordion  [P2 WIP]
Footer        — «Есть задача?» + @rcnn43
/en           — EN mirror (content из lib/content/en.ts)  [P2 WIP]
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
| 2026-06-20 | P2 WIP: WhyMe + FAQ + `/en` + 6 services · build ✅ · prod ещё P1 · metadataBase fix pending |



_Старые § — `docs/team/archive/` при переносе Lead Architect._

