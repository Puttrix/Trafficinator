"""
Database module for configuration presets and funnels.

SQLite database for storing and managing configuration presets and funnel definitions.
"""
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_DB_PATH = Path(
    os.getenv("CONFIG_DB_PATH", Path(__file__).resolve().parent / "data" / "presets.db")
)


class Database:
    """SQLite database manager for configuration presets and funnels."""

    def __init__(self, db_path: Optional[str] = None):
        resolved_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path = str(resolved_path)
        self.ensure_data_directory()
        self.init_schema()

    def ensure_data_directory(self):
        """Ensure data directory exists."""
        data_dir = Path(self.db_path).parent
        data_dir.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self):
        """Initialize database schema."""
        with self.get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS config_presets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    config_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS funnels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    config_json TEXT NOT NULL,
                    probability REAL NOT NULL DEFAULT 0,
                    priority INTEGER NOT NULL DEFAULT 0,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    # -------------------------------------------------------------------------
    # Presets
    # -------------------------------------------------------------------------
    def list_presets(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, name, description, created_at, updated_at
                FROM config_presets
                ORDER BY updated_at DESC
                """
            )

            presets = []
            for row in cursor.fetchall():
                presets.append(
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "description": row["description"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                    }
                )

            return presets

    def get_preset(self, preset_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, name, description, config_json, created_at, updated_at
                FROM config_presets
                WHERE id = ?
                """,
                (preset_id,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            return {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "config": json.loads(row["config_json"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

    def create_preset(
        self,
        name: str,
        config: Dict[str, Any],
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        config_json = json.dumps(config)

        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO config_presets (name, description, config_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, description, config_json, now, now),
            )

            conn.commit()
            preset_id = cursor.lastrowid

        return self.get_preset(preset_id)

    def update_preset(
        self,
        preset_id: int,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        existing = self.get_preset(preset_id)
        if not existing:
            return None

        updates = []
        params: List[Any] = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)

        if config is not None:
            updates.append("config_json = ?")
            params.append(json.dumps(config))

        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if not updates:
            return existing

        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())

        params.append(preset_id)

        with self.get_connection() as conn:
            conn.execute(
                f"""
                UPDATE config_presets
                SET {', '.join(updates)}
                WHERE id = ?
                """,
                params,
            )
            conn.commit()

        return self.get_preset(preset_id)

    def delete_preset(self, preset_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                DELETE FROM config_presets
                WHERE id = ?
                """,
                (preset_id,),
            )
            conn.commit()

            return cursor.rowcount > 0

    # -------------------------------------------------------------------------
    # Funnels
    # -------------------------------------------------------------------------
    def list_funnels(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, name, description, probability, priority, enabled, config_json, created_at, updated_at
                FROM funnels
                ORDER BY priority ASC, updated_at DESC
                """
            )

            funnels: List[Dict[str, Any]] = []
            for row in cursor.fetchall():
                config = json.loads(row["config_json"])
                steps = config.get("steps", [])
                funnels.append(
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "description": row["description"],
                        "probability": row["probability"],
                        "priority": row["priority"],
                        "enabled": bool(row["enabled"]),
                        "step_count": len(steps),
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                    }
                )
            return funnels

    def get_funnels_for_export(self, only_enabled: bool = True) -> List[Dict[str, Any]]:
        """
        Retrieve funnels including full configuration payload for export.

        Args:
            only_enabled: When True, filter to funnels marked as enabled.

        Returns:
            List of funnel dictionaries ready to serialize to JSON.
        """
        query = """
            SELECT name, description, probability, priority, enabled, config_json, updated_at
            FROM funnels
        """
        if only_enabled:
            query += " WHERE enabled = 1"
        query += " ORDER BY priority ASC, updated_at DESC"

        funnels: List[Dict[str, Any]] = []
        with self.get_connection() as conn:
            cursor = conn.execute(query)
            for row in cursor.fetchall():
                config = json.loads(row["config_json"])
                steps = config.get("steps", [])
                if not steps:
                    continue

                funnel = {
                    "name": row["name"],
                    "description": row["description"],
                    "probability": row["probability"],
                    "priority": row["priority"],
                    "enabled": bool(row["enabled"]),
                    "exit_after_completion": bool(config.get("exit_after_completion", True)),
                    "steps": steps,
                }
                funnels.append(funnel)

        return funnels

    def get_funnel(self, funnel_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, name, description, probability, priority, enabled, config_json, created_at, updated_at
                FROM funnels
                WHERE id = ?
                """,
                (funnel_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            config = json.loads(row["config_json"])
            return {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "probability": row["probability"],
                "priority": row["priority"],
                "enabled": bool(row["enabled"]),
                "config": config,
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

    def create_funnel(
        self,
        name: str,
        description: Optional[str],
        config: Dict[str, Any],
        probability: float,
        priority: int,
        enabled: bool,
    ) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        config_json = json.dumps(config)

        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO funnels (name, description, config_json, probability, priority, enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    description,
                    config_json,
                    probability,
                    priority,
                    1 if enabled else 0,
                    now,
                    now,
                ),
            )
            conn.commit()
            funnel_id = cursor.lastrowid

        return self.get_funnel(funnel_id)  # type: ignore[return-value]

    def update_funnel(
        self,
        funnel_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        probability: Optional[float] = None,
        priority: Optional[int] = None,
        enabled: Optional[bool] = None,
    ) -> Optional[Dict[str, Any]]:
        existing = self.get_funnel(funnel_id)
        if not existing:
            return None

        updates = []
        params: List[Any] = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)

        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if config is not None:
            updates.append("config_json = ?")
            params.append(json.dumps(config))

        if probability is not None:
            updates.append("probability = ?")
            params.append(probability)

        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)

        if enabled is not None:
            updates.append("enabled = ?")
            params.append(1 if enabled else 0)

        if not updates:
            return existing

        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(funnel_id)

        with self.get_connection() as conn:
            conn.execute(
                f"""
                UPDATE funnels
                SET {', '.join(updates)}
                WHERE id = ?
                """,
                params,
            )
            conn.commit()

        return self.get_funnel(funnel_id)

    def delete_funnel(self, funnel_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                DELETE FROM funnels
                WHERE id = ?
                """,
                (funnel_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
