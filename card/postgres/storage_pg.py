"""
PostgreSQL storage layer for transport cards system.
Drop-in replacement for JSON storage (storage.py).

Usage:
    from postgres.storage_pg import PostgreSQLStorage
    storage = PostgreSQLStorage()
    # Then use the same API as JSON storage
"""
import os
import uuid
import json
from datetime import datetime
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    raise ImportError("psycopg2 is required. Install: pip install psycopg2-binary")

# ============== JSON ADAPTERS ==============#

# Global JSON fields mapping: table_name -> set of JSON column names
JSON_COLUMNS = {
    "employees": {"roles", "permissions"},
    "documents": {"lines"},
}

# ============== DATABASE CONFIG ==============#
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "database": os.environ.get("DB_NAME", "transport_cards"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "postgres"),
}

@contextmanager
def get_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

@contextmanager
def get_cursor(dict_cursor=False):
    with get_connection() as conn:
        cursor_factory = RealDictCursor if dict_cursor else None
        cur = conn.cursor(cursor_factory=cursor_factory)
        try:
            yield cur
        finally:
            cur.close()

# ============== JSON HELPERS ==============#

def _serialize_json_fields(table, item):
    """Convert dict/list fields to JSON strings for PostgreSQL."""
    json_cols = JSON_COLUMNS.get(table, set())
    result = {}
    for key, value in item.items():
        if key in json_cols and value is not None and not isinstance(value, str):
            result[key] = json.dumps(value, ensure_ascii=False)
        else:
            result[key] = value
    return result

def _deserialize_json_fields(table, item):
    """Convert JSON strings back to Python objects from PostgreSQL."""
    if item is None:
        return None
    json_cols = JSON_COLUMNS.get(table, set())
    result = dict(item)
    for key in json_cols:
        if key in result and result[key] is not None:
            if isinstance(result[key], str):
                try:
                    result[key] = json.loads(result[key])
                except (json.JSONDecodeError, TypeError):
                    pass
    return result

# ============== STORAGE CLASS ==============#

class PostgreSQLStorage:
    TABLE_MAP = {
        "cards": "cards",
        "card_types": "card_types",
        "owners": "owners",
        "applicants": "applicants",
        "organizations": "organizations",
        "mfcs": "mfcs",
        "employees": "employees",
        "documents": "documents",
        "action_log": "action_log",
        "constants": "constants",
        "counters": "counters",
    }

    def load_all(self, name):
        table = self.TABLE_MAP.get(name, name)
        with get_cursor(dict_cursor=True) as cur:
            cur.execute(f"SELECT * FROM {table} ORDER BY created_at")
            rows = cur.fetchall()
            return [_deserialize_json_fields(table, dict(row)) for row in rows]

    def save_all(self, name, data):
        pass

    def find_one(self, name, predicate):
        items = self.load_all(name)
        for item in items:
            if predicate(item):
                return item
        return None

    def find_many(self, name, predicate):
        items = self.load_all(name)
        return [item for item in items if predicate(item)]

    def insert(self, name, item):
        table = self.TABLE_MAP.get(name, name)
        if "id" not in item or not item["id"]:
            item["id"] = str(uuid.uuid4())
        item["created_at"] = datetime.now().isoformat()

        serialized_item = _serialize_json_fields(table, item)

        columns = list(serialized_item.keys())
        values = list(serialized_item.values())
        placeholders = ["%s"] * len(values)

        sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING *"

        with get_cursor(dict_cursor=True) as cur:
            cur.execute(sql, values)
            row = cur.fetchone()
            return _deserialize_json_fields(table, dict(row)) if row else item

    def update(self, name, predicate, updates):
        table = self.TABLE_MAP.get(name, name)
        updates["updated_at"] = datetime.now().isoformat()

        items = self.load_all(name)
        for item in items:
            if predicate(item):
                serialized_updates = _serialize_json_fields(table, updates)
                set_clause = ", ".join([f"{k} = %s" for k in serialized_updates.keys()])
                sql = f"UPDATE {table} SET {set_clause} WHERE id = %s"
                values = list(serialized_updates.values()) + [item["id"]]

                with get_cursor() as cur:
                    cur.execute(sql, values)

                item.update(updates)
                return item
        return None

    def delete(self, name, predicate):
        table = self.TABLE_MAP.get(name, name)
        items = self.load_all(name)
        for item in items:
            if predicate(item):
                sql = f"DELETE FROM {table} WHERE id = %s"
                with get_cursor() as cur:
                    cur.execute(sql, (item["id"],))

    def get_next_number(self, prefix, name="counters"):
        table = self.TABLE_MAP.get(name, name)
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT pg_advisory_lock(hashtext(%s))", (prefix,))
            try:
                cur.execute(f"SELECT value FROM {table} WHERE prefix = %s FOR UPDATE", (prefix,))
                row = cur.fetchone()
                if row:
                    value = row[0] + 1
                    cur.execute(f"UPDATE {table} SET value = %s WHERE prefix = %s", (value, prefix))
                else:
                    value = 1
                    cur.execute(f"INSERT INTO {table} (prefix, value) VALUES (%s, %s)", (prefix, value))
                conn.commit()
                return f"{prefix}-{value:06d}"
            finally:
                cur.execute("SELECT pg_advisory_unlock(hashtext(%s))", (prefix,))
                cur.close()

# ============== COMPATIBILITY FUNCTIONS ==============#

_pg_storage = PostgreSQLStorage()

def load_all(name):
    return _pg_storage.load_all(name)

def save_all(name, data):
    return _pg_storage.save_all(name, data)

def find_one(name, predicate):
    return _pg_storage.find_one(name, predicate)

def find_many(name, predicate):
    return _pg_storage.find_many(name, predicate)

def insert(name, item):
    return _pg_storage.insert(name, item)

def update(name, predicate, updates):
    return _pg_storage.update(name, predicate, updates)

def delete(name, predicate):
    return _pg_storage.delete(name, predicate)

def get_next_number(prefix, name="counters"):
    return _pg_storage.get_next_number(prefix, name)
