# YouDo O268 — стабильный ingest (пробили)

**Дата:** 2026-06-18 ~14:26 UTC (первый успех после O268) · повторы до **2026-06-19 00:07 UTC**  
**Статус:** 🟢 **golden baseline** — откатываться сюда при регрессе YouDo

---

## Golden snapshot (VPS 2026-06-19)

| Артефакт | Путь | Факт |
|----------|------|------|
| Camoufox profile g2 | `/opt/rawlead/data/backups/youdo_profile_g2_2026-06-19.tar.gz` | **64M** |
| sha256 | `bd854d5cad868637973cf616e6ecd637153de34bb6cdf2e1e34078064022ef68` | verify перед restore |
| Лог-вырезка | `/opt/rawlead/data/backups/youdo_breakthrough_log_2026-06-19.txt` | эталонные строки |
| Live profile | `/opt/rawlead/data/youdo_185.147.131.15:8000_g2` | ~104M · **не удалять** |

**Правило для @coder / @mechanic:** при YouDo регрессе (1712b, ingest=0) — **сначала** сравнить с этим снимком и restore tar, **потом** менять код/env.

---

## Симптом «было»

- `html_len≈1700` — ServicePipe shell `/exhkqyad`, не SPA
- `youdo:ingest done=0` днями
- O267 sticky **reload trap** на отравленных cookies (1712b)

## Что сработало (O268)

| Механизм | Смысл |
|----------|--------|
| **Profile wipe + `YOUDO_PROFILE_GENERATION=2`** | чистый Camoufox profile `data/youdo_185.147.131.15:8000_g2` |
| **Ephemeral-first slot1** | первый заход «холодный», без ядовитых cookies |
| **`YOUDO_STICKY_AFTER_OK=1`** | после `html_len>100k` → sticky session на том же DC |
| **4× RU DC carousel** | `185.147.131.15`, `194.226.*` — без RU residential burst |
| **`YOUDO_SOFT_SERVICEPIPE_BAN`** | мягкий fail SP без 30min cooldown на весь парсер |
| **No reload-on-poison** | O267 reload trap убран в sticky worker |

**Победный прокси (повторяется):** `185.147.131.15:8000` · `tier=dc` · `slot=1/4` · `alive=4/4`

---

## Эталонная строка лога (2026-06-19 00:07:03 UTC)

```text
fetch:youdo proxy=185.147.131.15:8000 tier=dc slot=1/4 alive=4/4 ru_alive=25
youdo:trace stage=list_view clicked=0 data_id=50 selector=skip_has_cards
youdo:trace stage=sticky_goto goto_ms=13394 html_len=270998 proxy_hint=185.147.131.15:8000 warm=0
fetch:youdo outcome=ok reason=ok tier=dc parsed=50
youdo:ingest done=50 new=26
```

**Интерпретация:** sticky goto вернул **~271KB HTML** → 50 карточек → **26 новых** в PG.

До этого (00:01–00:03) — серия `antibot_hit=1 html_len=1701` на carousel (другие слоты / SP).

---

## Хронология ingest `done=50` (последние 10)

Из `radar_site.log` (2026-06-18 вечер):

| new | примечание |
|-----|------------|
| 40 | крупный пакет |
| 27 | |
| 11 | |
| 19 | |
| 26 | последний зафиксированный бэкапом |

Между циклами radar: `fetch_every_n=4` → `youdo:skip` — **норма**, не регресс.

---

## Что сохранить (✅ Lead 2026-06-19)

На VPS `/opt/rawlead/data/backups/`:

| Артефакт | Путь | Факт |
|----------|------|------|
| **Профиль Camoufox g2** | `youdo_profile_g2_2026-06-19.tar.gz` | **64M** |
| sha256 | `bd854d5cad868637973cf616e6ecd637153de34bb6cdf2e1e34078064022ef68` | |
| **Вырезка лога** | `youdo_breakthrough_log_2026-06-19.txt` | ~1.5K |
| Debug antibot (если нужен diff) | `data/debug_listings/youdo_antibot_*.html` |

**Не делать без бэкапа:**

- `rm -rf /opt/rawlead/data/youdo_*`
- смена `YOUDO_PROFILE_GENERATION`
- deploy O269+ с wipe profile
- hard reset YouDo из `/ops/` «на всякий случай»

---

## Восстановление профиля (если снесли)

```bash
cd /opt/rawlead/data
# verify: sha256sum backups/youdo_profile_g2_2026-06-19.tar.gz
sudo -u rawlead tar -xzf backups/youdo_profile_g2_2026-06-19.tar.gz
systemctl restart rawlead-radar
```

Код O268 уже в repo: `exchange_browser_fetch.py` · `deploy-o268-youdo-recovery-vps.py`.

---

## Watch 48h

- [ ] `grep 'outcome=ok parsed=50' radar_site.log` ≥1 раз / ~15 min активного fetch
- [ ] `ingest done=50` с `new>0` хотя бы раз в сутки
- [ ] профиль `youdo_185.147.131.15:8000_g2` на диске · `cookies.sqlite` > 512B
- [ ] при откате к 1712b → **не** менять всё сразу: сначала carousel, потом profile restore из tar

---

## Связано

- Родительский тикет: [`2026-06-16-youdo-antibot-browser.md`](2026-06-16-youdo-antibot-browser.md) § O268
- STATUS § O268
- CODER_PROMPT § O268 closed (watch)
