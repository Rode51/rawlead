"""SQLite: уже виденные проекты (дедуп по паре source + project_id)."""



from __future__ import annotations



import os
import sqlite3

from pathlib import Path



from config import Config



SOURCE_FL_DEFAULT = "fl"





class ProjectStorage:

    """Таблица `projects`: один ряд на (source, project_id)."""



    def __init__(self, db_path: Path) -> None:

        self._db_path = Path(db_path)

        parent = self._db_path.parent

        if str(parent) not in ("", "."):

            parent.mkdir(parents=True, exist_ok=True)

        self._ensure_schema()



    def _connect(self) -> sqlite3.Connection:

        conn = sqlite3.connect(self._db_path)

        conn.row_factory = sqlite3.Row

        return conn



    def _table_columns(self, conn: sqlite3.Connection) -> dict[str, str]:

        rows = conn.execute("PRAGMA table_info(projects)").fetchall()

        return {str(r["name"]): str(r["type"]) for r in rows}



    def _migrate_legacy_project_id_only(self, conn: sqlite3.Connection) -> None:

        cols = self._table_columns(conn)

        if not cols or "source" in cols:

            return

        conn.execute("ALTER TABLE projects RENAME TO projects_legacy")

        conn.execute(

            """

            CREATE TABLE projects (

                source TEXT NOT NULL,

                project_id INTEGER NOT NULL,

                first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),

                PRIMARY KEY (source, project_id)

            )

            """

        )

        conn.execute(

            """

            INSERT INTO projects (source, project_id, first_seen_at)

            SELECT ?, project_id, first_seen_at FROM projects_legacy

            """,

            (SOURCE_FL_DEFAULT,),

        )

        conn.execute("DROP TABLE projects_legacy")

        conn.commit()

    def _migrate_neon_synced_columns(self, conn: sqlite3.Connection) -> None:
        cols = self._table_columns(conn)
        if "neon_synced_at" not in cols:
            conn.execute("ALTER TABLE projects ADD COLUMN neon_synced_at TEXT")
        if "neon_synced_hash" not in cols:
            conn.execute("ALTER TABLE projects ADD COLUMN neon_synced_hash TEXT")
        conn.commit()

    def _ensure_schema(self) -> None:

        with self._connect() as conn:

            conn.execute(

                """

                CREATE TABLE IF NOT EXISTS projects (

                    source TEXT NOT NULL,

                    project_id INTEGER NOT NULL,

                    first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),

                    PRIMARY KEY (source, project_id)

                )

                """

            )

            conn.execute(

                """

                CREATE TABLE IF NOT EXISTS settings (

                    key TEXT PRIMARY KEY,

                    value TEXT NOT NULL

                )

                """

            )

            conn.execute(

                """

                CREATE TABLE IF NOT EXISTS listing_fingerprints (

                    content_hash TEXT PRIMARY KEY,

                    first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),

                    first_source TEXT NOT NULL DEFAULT ''

                )

                """

            )

            conn.commit()

            self._migrate_legacy_project_id_only(conn)
            self._migrate_neon_synced_columns(conn)



    def get_setting(self, key: str, default: str = "") -> str:

        with self._connect() as conn:

            row = conn.execute(

                "SELECT value FROM settings WHERE key = ? LIMIT 1",

                (key,),

            ).fetchone()

            if row is None:

                return default

            return str(row["value"])



    def set_setting(self, key: str, value: str) -> None:

        with self._connect() as conn:

            conn.execute(

                """

                INSERT INTO settings (key, value) VALUES (?, ?)

                ON CONFLICT(key) DO UPDATE SET value = excluded.value

                """,

                (key, value),

            )

            conn.commit()



    def incr_setting(self, key: str, delta: int = 1) -> None:

        current = self.get_setting(key, "0")

        try:

            value = int(current.strip() or "0") + delta

        except ValueError:

            value = delta

        self.set_setting(key, str(value))



    _PAUSE_KEY_LEGACY = "radar_paused_legacy"
    _PAUSE_KEY_SITE = "radar_paused_site"
    _PAUSE_KEY_SHARED = "radar_paused"

    @classmethod
    def _pause_setting_key(cls) -> str:
        profile = os.environ.get("RADAR_PROFILE", "legacy").strip().casefold()
        return cls._PAUSE_KEY_SITE if profile == "site" else cls._PAUSE_KEY_LEGACY

    def _has_setting(self, key: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM settings WHERE key = ? LIMIT 1",
                (key,),
            ).fetchone()
            return row is not None

    def is_radar_paused(self) -> bool:
        key = self._pause_setting_key()
        if self._has_setting(key):
            return self.get_setting(key, "0") == "1"
        return self.get_setting(self._PAUSE_KEY_SHARED, "0") == "1"

    def set_radar_paused(self, paused: bool) -> None:
        self.set_setting(self._pause_setting_key(), "1" if paused else "0")
        if self._has_setting(self._PAUSE_KEY_SHARED):
            self.set_setting(self._PAUSE_KEY_SHARED, "0")



    @staticmethod
    def tg_update_offset_key(bot_token: str) -> str:
        token = (bot_token or "").strip()
        bot_id = token.split(":", 1)[0] if token else ""
        if bot_id.isdigit():
            return f"tg_update_offset:{bot_id}"
        return "tg_update_offset:unknown"

    def has_tg_update_offset_key(self, bot_token: str) -> bool:
        key = self.tg_update_offset_key(bot_token)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM settings WHERE key = ? LIMIT 1",
                (key,),
            ).fetchone()
            return row is not None

    def get_tg_update_offset(self, *, bot_token: str) -> int:
        key = self.tg_update_offset_key(bot_token)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = ? LIMIT 1",
                (key,),
            ).fetchone()
            if row is not None:
                raw = str(row["value"])
            else:
                raw = self.get_setting("tg_update_offset", "0")
        try:
            return max(0, int(raw))
        except ValueError:
            return 0

    def set_tg_update_offset(self, offset: int, *, bot_token: str) -> None:
        key = self.tg_update_offset_key(bot_token)
        self.set_setting(key, str(max(0, offset)))



    def has_seen(self, source: str, project_id: int) -> bool:

        """Уже есть запись с этой парой (source, project_id)."""

        with self._connect() as conn:

            row = conn.execute(

                "SELECT 1 FROM projects WHERE source = ? AND project_id = ? LIMIT 1",

                (source, project_id),

            ).fetchone()

            return row is not None

    def max_project_id(self, source: str) -> int:
        """MAX(project_id) для источника в SQLite (watermark для Пчёл)."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT MAX(project_id) FROM projects WHERE source = ?",
                (source,),
            ).fetchone()
        if not row or row[0] is None:
            return 0
        try:
            return int(row[0])
        except (TypeError, ValueError):
            return 0

    def list_project_ids(self, sources: list[str]) -> list[tuple[str, int]]:
        """Все (source, project_id) из SQLite для указанных источников."""
        if not sources:
            return []
        placeholders = ",".join("?" * len(sources))
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT source, project_id FROM projects
                WHERE source IN ({placeholders})
                ORDER BY source, project_id
                """,
                tuple(sources),
            ).fetchall()
        out: list[tuple[str, int]] = []
        for row in rows:
            try:
                out.append((str(row["source"]), int(row["project_id"])))
            except (TypeError, ValueError):
                continue
        return out



    def try_record_new(self, source: str, project_id: int) -> bool:

        """

        Записать пару (source, project_id), если её ещё не было.

        True — вставлена новая строка; False — дубль.

        """

        with self._connect() as conn:

            cur = conn.execute(

                "INSERT OR IGNORE INTO projects (source, project_id) VALUES (?, ?)",

                (source, project_id),

            )

            conn.commit()

            return cur.rowcount == 1

    def get_neon_synced_hash(self, source: str, project_id: int) -> str:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT neon_synced_hash FROM projects
                WHERE source = ? AND project_id = ?
                LIMIT 1
                """,
                (source, project_id),
            ).fetchone()
        if row is None or row["neon_synced_hash"] is None:
            return ""
        return str(row["neon_synced_hash"]).strip()

    def is_neon_dup_fast_path(
        self, source: str, project_id: int, content_hash: str
    ) -> bool:
        """Локально известно: dup в SQLite, тот же текст, Neon+L1 уже синхронизированы."""
        h = (content_hash or "").strip()
        if not h:
            return False
        synced_hash = self.get_neon_synced_hash(source, project_id)
        if not synced_hash or synced_hash != h:
            return False
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT neon_synced_at FROM projects
                WHERE source = ? AND project_id = ?
                LIMIT 1
                """,
                (source, project_id),
            ).fetchone()
        return row is not None and bool(row["neon_synced_at"])

    def mark_neon_dup_synced(
        self, source: str, project_id: int, content_hash: str
    ) -> None:
        h = (content_hash or "").strip()
        if not h:
            return
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE projects
                SET neon_synced_at = datetime('now'), neon_synced_hash = ?
                WHERE source = ? AND project_id = ?
                """,
                (h, source, project_id),
            )
            conn.commit()

    def clear_neon_dup_synced(self, source: str, project_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE projects
                SET neon_synced_at = NULL, neon_synced_hash = NULL
                WHERE source = ? AND project_id = ?
                """,
                (source, project_id),
            )
            conn.commit()

    def try_record_content_fingerprint(self, content_hash: str, *, source: str = "") -> bool:

        """True — новый текст; False — такое объявление уже было."""

        h = (content_hash or "").strip()

        if not h:

            return True

        with self._connect() as conn:

            cur = conn.execute(

                """

                INSERT OR IGNORE INTO listing_fingerprints (content_hash, first_source)

                VALUES (?, ?)

                """,

                (h, (source or "").strip()),

            )

            conn.commit()

            return cur.rowcount == 1





def storage_from_config(cfg: Config) -> ProjectStorage:

    """Хранилище по пути `cfg.sqlite_path` (из SQLITE_PATH / дефолт в config)."""

    return ProjectStorage(cfg.sqlite_path)

