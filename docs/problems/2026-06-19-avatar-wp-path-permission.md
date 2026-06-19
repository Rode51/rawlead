# Avatar 404 после O280 Next cutover

**Дата:** 2026-06-19  
**Симптом:** header — жёлтый круг с буквой · `GET /v1/me/avatar` → **404**  
**Кто:** owner (user `00000000-0000-0000-0000-000000000001`)

## Причина

O185 deploy прописал в `.env.site`:

`RAWLEAD_AVATAR_DIR=/var/www/rawlead.ru/wp-content/uploads/rawlead-avatars`

После cutover на Next `rawlead` API **не может писать** в `wp-content`:

```
avatar cache failed user=...: [Errno 13] Permission denied: '/var/www/rawlead.ru/wp-content'
GET /v1/me/avatar HTTP/1.1" 404
```

Каталог `/opt/rawlead/data/avatars/` **не создан** — env тянет WP path.

Фронт (R9) ок: CORS `https://rawlead.ru` ✅ · `resolveAvatarSrc` → `/me/avatar` ✅.

## Fix (2026-06-19 R9b)

`.env.site` → `/opt/rawlead/data/avatars` · guard в `user_avatar.py` · owner jpg cached ✅

1. `.env.site`: `RAWLEAD_AVATAR_DIR=/opt/rawlead/data/avatars`
2. `mkdir -p /opt/rawlead/data/avatars && chown rawlead:rawlead`
3. Deploy `src/user_avatar.py` (repo) · `systemctl restart rawlead-api`
4. Owner: перелогин → cache on login

## Ref

`scripts/deploy-o185-w2-vps.py` L13–36 · `src/user_avatar.py` `_DEFAULT_DIR`
