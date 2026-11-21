"""Initialize/upgrade the development MySQL schema to the 40-table specification.

Safe behavior: never drops a database, table, row, or Docker volume. Existing
20-table installations are extended in place. Run with: python -m scripts.init_db
"""
from __future__ import annotations

import re
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from app.core.config import get_settings

SCHEMA_FILE = Path(__file__).resolve().parents[1] / "sql" / "00_schema_40_tables.sql"
EXPECTED_TABLES = 40


def _statements(source: str) -> list[str]:
    # The schema file intentionally contains plain DDL only (no stored routines).
    cleaned = "\n".join(
        line for line in source.splitlines()
        if not line.lstrip().startswith("--")
    )
    return [part.strip() for part in cleaned.split(";") if part.strip()]


def _apply_statement(conn, statement: str, schema: str) -> None:
    upper = statement.upper()

    # The database is created explicitly before connecting; USE/CREATE DATABASE
    # are not needed here and can cause multi-statement/permission surprises.
    if upper.startswith("CREATE DATABASE") or upper.startswith("USE "):
        return
    if upper.startswith("SET FOREIGN_KEY_CHECKS"):
        conn.exec_driver_sql(statement)
        return

    # Make generated-column and unique-index additions repeatable on an
    # existing 20-table installation or after an interrupted initialization.
    if upper.startswith("ALTER TABLE") and " ADD COLUMN " in upper:
        m = re.search(r"ALTER TABLE `([^`]+)` ADD COLUMN `([^`]+)`", statement, re.I)
        if m:
            table, column = m.groups()
            exists = conn.execute(text("""SELECT COUNT(*) FROM information_schema.columns
                WHERE table_schema=:s AND table_name=:t AND column_name=:c"""),
                {"s": schema, "t": table, "c": column}).scalar_one()
            if exists:
                return

    if upper.startswith("ALTER TABLE") and " ADD UNIQUE KEY " in upper:
        m = re.search(r"ALTER TABLE `([^`]+)` ADD UNIQUE KEY `([^`]+)`", statement, re.I)
        if m:
            table, index_name = m.groups()
            exists = conn.execute(text("""SELECT COUNT(*) FROM information_schema.statistics
                WHERE table_schema=:s AND table_name=:t AND index_name=:i"""),
                {"s": schema, "t": table, "i": index_name}).scalar_one()
            if exists:
                return

    # CHECK constraints are named in the DDL and can be checked idempotently.
    if upper.startswith("ALTER TABLE") and " ADD CONSTRAINT " in upper and " CHECK " in upper:
        m = re.search(r"ALTER TABLE `([^`]+)` ADD CONSTRAINT `([^`]+)` CHECK", statement, re.I)
        if m:
            table, constraint_name = m.groups()
            exists = conn.execute(text("""SELECT COUNT(*) FROM information_schema.table_constraints
                WHERE constraint_schema=:s AND table_name=:t AND constraint_name=:c
                  AND constraint_type='CHECK'"""),
                {"s": schema, "t": table, "c": constraint_name}).scalar_one()
            if exists:
                return

    # Skip a foreign key already present by its column relationship, even if
    # the old SQLAlchemy-created constraint has a different generated name.
    if upper.startswith("ALTER TABLE") and " ADD CONSTRAINT " in upper and " FOREIGN KEY " in upper:
        m = re.search(
            r"ALTER TABLE `([^`]+)` ADD CONSTRAINT `[^`]+` FOREIGN KEY \(`([^`]+)`\) REFERENCES `([^`]+)` \(`([^`]+)`\)",
            statement, re.I,
        )
        if m:
            child, column, parent, refcol = m.groups()
            exists = conn.execute(text("""SELECT COUNT(*) FROM information_schema.key_column_usage
                WHERE constraint_schema=:s AND table_name=:child AND column_name=:col
                  AND referenced_table_name=:parent AND referenced_column_name=:ref"""),
                {"s": schema, "child": child, "col": column,
                 "parent": parent, "ref": refcol}).scalar_one()
            if exists:
                return

    # Make operational indexes repeatable.
    if upper.startswith("CREATE INDEX"):
        m = re.search(r"CREATE INDEX `([^`]+)` ON `([^`]+)`", statement, re.I)
        if m:
            idx, table = m.groups()
            exists = conn.execute(text("""SELECT COUNT(*) FROM information_schema.statistics
                WHERE table_schema=:s AND table_name=:t AND index_name=:i"""),
                {"s": schema, "t": table, "i": idx}).scalar_one()
            if exists:
                return

    conn.exec_driver_sql(statement)


def main() -> None:
    settings = get_settings()
    if not settings.mysql_root_password:
        raise RuntimeError("MYSQL_ROOT_PASSWORD chưa được cấu hình trong .env")

    admin_url = URL.create(
        "mysql+pymysql", username="root", password=settings.mysql_root_password,
        host=settings.db_server, port=settings.db_port,
        query={"charset": "utf8mb4"},
    )
    admin = create_engine(admin_url, pool_pre_ping=True, isolation_level="AUTOCOMMIT")
    schema = settings.db_name
    safe_schema = schema.replace("`", "``")

    try:
        with admin.connect() as conn:
            conn.exec_driver_sql(
                f"CREATE DATABASE IF NOT EXISTS `{safe_schema}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        db_url = admin_url.set(database=schema)
        db = create_engine(db_url, pool_pre_ping=True, isolation_level="AUTOCOMMIT")
        try:
            ddl = SCHEMA_FILE.read_text(encoding="utf-8")
            with db.connect() as conn:
                for statement in _statements(ddl):
                    _apply_statement(conn, statement, schema)

                tables = conn.execute(text("""SELECT COUNT(*) FROM information_schema.tables
                    WHERE table_schema=:s AND table_type='BASE TABLE'"""), {"s": schema}).scalar_one()
                fk_count = conn.execute(text("""SELECT COUNT(*) FROM information_schema.table_constraints
                    WHERE constraint_schema=:s AND constraint_type='FOREIGN KEY'"""), {"s": schema}).scalar_one()
                if tables != EXPECTED_TABLES:
                    raise RuntimeError(
                        f"Schema chưa hoàn chỉnh: tìm thấy {tables}/{EXPECTED_TABLES} bảng. "
                        "Xem log lỗi SQL phía trên; dữ liệu hiện có không bị xóa."
                    )
                print(f"OK: database '{schema}' sẵn sàng: {tables}/{EXPECTED_TABLES} bảng, {fk_count} khóa ngoại.")
        finally:
            db.dispose()
    finally:
        admin.dispose()


if __name__ == "__main__":
    main()
