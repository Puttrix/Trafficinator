"""
Database module for configuration presets

SQLite database for storing and managing configuration presets.
"""
import os
import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

DEFAULT_DB_PATH = Path(
    os.getenv("CONFIG_DB_PATH", Path(__file__).resolve().parent / "data" / "presets.db")
)


class Database:
    """SQLite database manager for configuration presets"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        resolved_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path = str(resolved_path)
        self.ensure_data_directory()
        self.init_schema()
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        data_dir = Path(self.db_path).parent
        data_dir.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def init_schema(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS config_presets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    config_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()
    
    def list_presets(self) -> List[Dict[str, Any]]:
        """
        Get all configuration presets
        
        Returns:
            List of preset dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, name, description, created_at, updated_at
                FROM config_presets
                ORDER BY updated_at DESC
            """)
            
            presets = []
            for row in cursor.fetchall():
                presets.append({
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                })
            
            return presets
    
    def get_preset(self, preset_id: int) -> Optional[Dict[str, Any]]:
        """
        Get specific configuration preset by ID
        
        Args:
            preset_id: Preset ID
        
        Returns:
            Preset dictionary with config, or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, name, description, config_json, created_at, updated_at
                FROM config_presets
                WHERE id = ?
            """, (preset_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "config": json.loads(row["config_json"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
    
    def create_preset(
        self,
        name: str,
        config: Dict[str, Any],
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create new configuration preset
        
        Args:
            name: Preset name
            config: Configuration dictionary
            description: Optional description
        
        Returns:
            Created preset dictionary
        
        Raises:
            sqlite3.IntegrityError: If name already exists
        """
        now = datetime.utcnow().isoformat()
        config_json = json.dumps(config)
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO config_presets (name, description, config_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (name, description, config_json, now, now))
            
            conn.commit()
            preset_id = cursor.lastrowid
        
        return self.get_preset(preset_id)
    
    def update_preset(
        self,
        preset_id: int,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update existing configuration preset
        
        Args:
            preset_id: Preset ID to update
            name: Optional new name
            config: Optional new configuration
            description: Optional new description
        
        Returns:
            Updated preset dictionary, or None if not found
        
        Raises:
            sqlite3.IntegrityError: If new name already exists
        """
        # Get existing preset
        existing = self.get_preset(preset_id)
        if not existing:
            return None
        
        # Prepare updates
        updates = []
        params = []
        
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
            return existing  # No changes
        
        # Add updated_at
        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        
        # Add preset_id for WHERE clause
        params.append(preset_id)
        
        with self.get_connection() as conn:
            conn.execute(f"""
                UPDATE config_presets
                SET {', '.join(updates)}
                WHERE id = ?
            """, params)
            conn.commit()
        
        return self.get_preset(preset_id)
    
    def delete_preset(self, preset_id: int) -> bool:
        """
        Delete configuration preset
        
        Args:
            preset_id: Preset ID to delete
        
        Returns:
            True if deleted, False if not found
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM config_presets
                WHERE id = ?
            """, (preset_id,))
            conn.commit()
            
            return cursor.rowcount > 0
