"""Cross-database compatible column types.

Uses PostgreSQL-native types when available (UUID, JSONB),
falls back to generic types (String, JSON) for SQLite.
"""
from __future__ import annotations

import uuid
import json
from sqlalchemy import String, Text, JSON, TypeDecorator
from sqlalchemy.engine import Connection

from core.config import settings

_IS_PG = settings.DATABASE_URL.startswith("postgresql")


if _IS_PG:
    from sqlalchemy.dialects.postgresql import UUID as _PG_UUID, JSONB as _PG_JSONB

    class GUID(_PG_UUID):
        """PostgreSQL UUID type."""
        def __init__(self, *args, **kwargs):
            kwargs.setdefault("as_uuid", True)
            super().__init__(*args, **kwargs)

    class JSONDict(_PG_JSONB):
        """PostgreSQL JSONB type."""
        pass

else:
    class GUID(TypeDecorator):
        """Cross-platform UUID type stored as String(36)."""
        impl = String(36)
        cache_ok = True

        def process_bind_param(self, value, dialect):
            if value is not None:
                return str(value)
            return value

        def process_result_value(self, value, dialect):
            if value is not None:
                return uuid.UUID(value)
            return value

    class JSONDict(TypeDecorator):
        """Cross-platform JSON type stored as Text."""
        impl = Text
        cache_ok = True

        def process_bind_param(self, value, dialect):
            if value is not None:
                return json.dumps(value, ensure_ascii=False)
            return value

        def process_result_value(self, value, dialect):
            if value is not None:
                return json.loads(value)
            return value


def uuid_default() -> str:
    """Generate a UUID4 string as server-side default replacement."""
    return str(uuid.uuid4())
