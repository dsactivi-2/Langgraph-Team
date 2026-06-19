from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .models import BuildResponse
from .settings import get_settings


class StorageUnavailable(RuntimeError):
    pass


class PostgresStore:
    def __init__(self, dsn: str | None = None) -> None:
        self.dsn = dsn or get_settings().postgres_dsn

    def _connect(self):
        return psycopg.connect(self.dsn, autocommit=True, row_factory=dict_row, connect_timeout=2)

    def setup(self) -> None:
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS builder_builds (
                        project_id TEXT PRIMARY KEY,
                        payload JSONB NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        id BIGSERIAL PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS chat_messages_project_created_idx
                    ON chat_messages(project_id, created_at)
                    """
                )
        except Exception as exc:  # pragma: no cover - exercised by fallback tests
            raise StorageUnavailable(str(exc)) from exc

    def save_build(self, response: BuildResponse) -> None:
        self.setup()
        payload = response.model_dump(mode="json")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO builder_builds(project_id, payload)
                VALUES (%s, %s)
                ON CONFLICT(project_id) DO UPDATE SET
                    payload = EXCLUDED.payload,
                    updated_at = now()
                """,
                (response.project_id, Jsonb(payload)),
            )

    def list_builds(self, limit: int = 25) -> list[BuildResponse]:
        self.setup()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT payload
                FROM builder_builds
                ORDER BY updated_at DESC
                LIMIT %s
                """,
                (limit,),
            ).fetchall()
        return [BuildResponse.model_validate(row["payload"]) for row in rows]

    def get_build(self, project_id: str) -> BuildResponse | None:
        self.setup()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM builder_builds WHERE project_id = %s",
                (project_id,),
            ).fetchone()
        return BuildResponse.model_validate(row["payload"]) if row else None

    def add_chat_message(self, project_id: str, role: str, content: str) -> dict[str, Any]:
        self.setup()
        with self._connect() as conn:
            row = conn.execute(
                """
                INSERT INTO chat_messages(project_id, role, content)
                VALUES (%s, %s, %s)
                RETURNING id, project_id, role, content, created_at
                """,
                (project_id, role, content),
            ).fetchone()
        return dict(row)

    def list_chat_messages(self, project_id: str, limit: int = 100) -> list[dict[str, Any]]:
        self.setup()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, project_id, role, content, created_at
                FROM chat_messages
                WHERE project_id = %s
                ORDER BY created_at ASC, id ASC
                LIMIT %s
                """,
                (project_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]


class HybridBuildArchive:
    def __init__(self, store: PostgresStore | None = None, max_items: int = 25) -> None:
        self.store = store or PostgresStore()
        self.max_items = max_items
        self._fallback_builds: list[BuildResponse] = []
        self._fallback_chat: list[dict[str, Any]] = []
        self.last_error: str | None = None

    def save_build(self, response: BuildResponse) -> None:
        try:
            self.store.save_build(response)
            self.last_error = None
        except StorageUnavailable as exc:
            self.last_error = str(exc)
            self._fallback_builds.insert(0, response)
            del self._fallback_builds[self.max_items :]

    def list_builds(self) -> list[BuildResponse]:
        try:
            builds = self.store.list_builds(self.max_items)
            self.last_error = None
            return builds
        except StorageUnavailable as exc:
            self.last_error = str(exc)
            return list(self._fallback_builds)

    def get_build(self, project_id: str) -> BuildResponse | None:
        try:
            build = self.store.get_build(project_id)
            self.last_error = None
            return build
        except StorageUnavailable as exc:
            self.last_error = str(exc)
            return next(
                (item for item in self._fallback_builds if item.project_id == project_id),
                None,
            )

    def add_chat_message(self, project_id: str, role: str, content: str) -> dict[str, Any]:
        try:
            message = self.store.add_chat_message(project_id, role, content)
            self.last_error = None
            return message
        except StorageUnavailable as exc:
            self.last_error = str(exc)
            message = {
                "id": len(self._fallback_chat) + 1,
                "project_id": project_id,
                "role": role,
                "content": content,
                "created_at": datetime.now(UTC),
            }
            self._fallback_chat.append(message)
            return message

    def list_chat_messages(self, project_id: str) -> list[dict[str, Any]]:
        try:
            messages = self.store.list_chat_messages(project_id)
            self.last_error = None
            return messages
        except StorageUnavailable as exc:
            self.last_error = str(exc)
            return [item for item in self._fallback_chat if item["project_id"] == project_id]
