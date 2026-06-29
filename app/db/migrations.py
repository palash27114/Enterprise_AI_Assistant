"""Liquibase-compatible SQL migrations executed on application startup."""

from __future__ import annotations

import hashlib
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

CHANGELOG_DIR = Path(__file__).resolve().parents[2] / "db" / "changelog"
MASTER_FILE = CHANGELOG_DIR / "db.changelog-master.yaml"

CHANGESET_PATTERN = re.compile(
    r"^--changeset\s+(?P<author>[\w.-]+):(?P<id>[\w.-]+)\s*$",
    re.MULTILINE,
)


@dataclass(frozen=True)
class ChangeSet:
    """Single Liquibase-formatted SQL changeset."""

    id: str
    author: str
    filename: str
    sql: str

    @property
    def key(self) -> str:
        return f"{self.author}:{self.id}"

    @property
    def md5sum(self) -> str:
        digest = hashlib.md5(self.sql.encode("utf-8")).hexdigest()
        return f"9:{digest}"


def _load_changelog_files() -> list[Path]:
    """Resolve ordered SQL changelog files from the master YAML."""
    if not MASTER_FILE.exists():
        raise FileNotFoundError(f"Changelog master not found: {MASTER_FILE}")

    with MASTER_FILE.open(encoding="utf-8") as handle:
        master = yaml.safe_load(handle)

    files: list[Path] = []
    for entry in master.get("databaseChangeLog", []):
        include = entry.get("include")
        if not include:
            continue
        relative = include.get("file")
        if not relative:
            continue
        path = (CHANGELOG_DIR / relative).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Changelog file not found: {path}")
        files.append(path)
    return files


def _parse_changesets(path: Path) -> list[ChangeSet]:
    """Parse a Liquibase formatted SQL file into changesets."""
    content = path.read_text(encoding="utf-8")
    if not content.lstrip().startswith("--liquibase formatted sql"):
        raise ValueError(f"Not a Liquibase formatted SQL file: {path}")

    matches = list(CHANGESET_PATTERN.finditer(content))
    if not matches:
        return []

    changesets: list[ChangeSet] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        sql = content[start:end].strip()
        changesets.append(
            ChangeSet(
                id=match.group("id"),
                author=match.group("author"),
                filename=str(path.relative_to(CHANGELOG_DIR.parent)),
                sql=sql,
            )
        )
    return changesets


def _split_sql_statements(sql: str) -> list[str]:
    """Split SQL on semicolons (safe for our migration scripts)."""
    statements: list[str] = []
    for part in sql.split(";"):
        statement = part.strip()
        if statement:
            statements.append(statement)
    return statements


def _ensure_liquibase_tables(connection) -> None:
    """Create Liquibase tracking tables if they do not exist."""
    ddl = """
    CREATE TABLE IF NOT EXISTS databasechangeloglock (
        id INTEGER NOT NULL PRIMARY KEY,
        locked BOOLEAN NOT NULL,
        lockgranted TIMESTAMP,
        lockedby VARCHAR(255)
    );

    CREATE TABLE IF NOT EXISTS databasechangelog (
        id VARCHAR(255) NOT NULL,
        author VARCHAR(255) NOT NULL,
        filename VARCHAR(255) NOT NULL,
        dateexecuted TIMESTAMP NOT NULL,
        orderexecuted INTEGER NOT NULL,
        exectype VARCHAR(10) NOT NULL,
        md5sum VARCHAR(35),
        description VARCHAR(255),
        comments VARCHAR(255),
        tag VARCHAR(255),
        liquibase VARCHAR(20),
        contexts VARCHAR(255),
        labels VARCHAR(255),
        deployment_id VARCHAR(10)
    );
    """
    for statement in _split_sql_statements(ddl):
        connection.execute(text(statement))
    connection.execute(
        text(
            """
            INSERT INTO databasechangeloglock (id, locked)
            VALUES (1, FALSE)
            ON CONFLICT (id) DO NOTHING
            """
        )
    )


def _is_applied(connection, changeset: ChangeSet) -> bool:
    result = connection.execute(
        text(
            """
            SELECT COUNT(*) FROM databasechangelog
            WHERE id = :id AND author = :author AND filename = :filename
            """
        ),
        {"id": changeset.id, "author": changeset.author, "filename": changeset.filename},
    )
    return int(result.scalar_one()) > 0


def _record_changeset(connection, changeset: ChangeSet, order: int) -> None:
    connection.execute(
        text(
            """
            INSERT INTO databasechangelog (
                id, author, filename, dateexecuted, orderexecuted,
                exectype, md5sum, description, liquibase
            ) VALUES (
                :id, :author, :filename, :dateexecuted, :orderexecuted,
                'EXECUTED', :md5sum, :description, 'app-startup'
            )
            """
        ),
        {
            "id": changeset.id,
            "author": changeset.author,
            "filename": changeset.filename,
            "dateexecuted": datetime.now(timezone.utc).replace(tzinfo=None),
            "orderexecuted": order,
            "md5sum": changeset.md5sum,
            "description": changeset.key,
        },
    )


def _release_lock(connection) -> None:
    connection.execute(
        text(
            """
            UPDATE databasechangeloglock
            SET locked = FALSE, lockgranted = NULL, lockedby = NULL
            WHERE id = 1
            """
        )
    )


def _apply_pending_migrations(connection) -> int:
    changelog_files = _load_changelog_files()
    all_changesets: list[ChangeSet] = []
    for path in changelog_files:
        all_changesets.extend(_parse_changesets(path))

    current_order = int(
        connection.execute(
            text("SELECT COALESCE(MAX(orderexecuted), 0) FROM databasechangelog")
        ).scalar_one()
    )

    applied = 0
    for changeset in all_changesets:
        if _is_applied(connection, changeset):
            continue

        logger.info("Running migration %s (%s)", changeset.key, changeset.filename)
        for statement in _split_sql_statements(changeset.sql):
            connection.execute(text(statement))

        current_order += 1
        _record_changeset(connection, changeset, current_order)
        applied += 1

    return applied


def run_migrations(engine: Engine, max_retries: int = 10, retry_delay: float = 3.0) -> None:
    """Apply pending Liquibase-formatted SQL changelogs on API startup."""
    for attempt in range(1, max_retries + 1):
        try:
            with engine.begin() as connection:
                _ensure_liquibase_tables(connection)

                locked = connection.execute(
                    text("SELECT locked FROM databasechangeloglock WHERE id = 1 FOR UPDATE")
                ).scalar_one()
                if locked:
                    raise RuntimeError("Database migration lock is already held.")

                connection.execute(
                    text(
                        """
                        UPDATE databasechangeloglock
                        SET locked = TRUE, lockgranted = NOW(), lockedby = 'enterprise-ai-api'
                        WHERE id = 1
                        """
                    )
                )

                try:
                    applied = _apply_pending_migrations(connection)
                finally:
                    _release_lock(connection)

            if applied:
                logger.info("Applied %s database migration(s)", applied)
            else:
                logger.info("Database schema is up to date")
            return
        except OperationalError as exc:
            if attempt == max_retries:
                logger.error("Database migration failed after %s attempts: %s", max_retries, exc)
                raise
            logger.warning(
                "Database not ready for migrations (attempt %s/%s), retrying in %ss...",
                attempt,
                max_retries,
                retry_delay,
            )
            time.sleep(retry_delay)
