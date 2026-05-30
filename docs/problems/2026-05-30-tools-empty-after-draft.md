# Tools пусто после draft (2026-05-30)

**Статус:** **→ @coder** § O37b b1  
**Симптом:** черновик есть · блок «Инструменты» = «появится после генерации отклика».

## Корень

Draft сохраняет текст, `tools_required` берётся из колонки lead в Neon (часто пусто) — L2 tools не пишутся при on-demand.

## Fix

→ [`CODER_PROMPT.md`](../team/architect/CODER_PROMPT.md) § **O37b** b1
