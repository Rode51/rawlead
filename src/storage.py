"""SQLite: уже виденные проекты (дедуп по паре source + project_id)."""



from __future__ import annotations



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



    def is_radar_paused(self) -> bool:

        return self.get_setting("radar_paused", "0") == "1"



    def set_radar_paused(self, paused: bool) -> None:

        self.set_setting("radar_paused", "1" if paused else "0")



    def get_tg_update_offset(self) -> int:

        raw = self.get_setting("tg_update_offset", "0")

        try:

            return max(0, int(raw))

        except ValueError:

            return 0



    def set_tg_update_offset(self, offset: int) -> None:

        self.set_setting("tg_update_offset", str(max(0, offset)))



    def has_seen(self, source: str, project_id: int) -> bool:

        """Уже есть запись с этой парой (source, project_id)."""

        with self._connect() as conn:

            row = conn.execute(

                "SELECT 1 FROM projects WHERE source = ? AND project_id = ? LIMIT 1",

                (source, project_id),

            ).fetchone()

            return row is not None



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

