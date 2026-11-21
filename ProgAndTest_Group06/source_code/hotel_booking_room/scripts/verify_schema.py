"""Verify the live MySQL schema against the 40-table specification."""
from sqlalchemy import create_engine, text
from app.core.config import get_settings
from app.data_access.models.specification import load_specification_models

EXPECTED_TABLES = 40
EXPECTED_FOREIGN_KEYS = 58


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            tables = conn.execute(text("""SELECT table_name FROM information_schema.tables
                WHERE table_schema=:schema AND table_type='BASE TABLE' ORDER BY table_name"""),
                {"schema": settings.db_name}).scalars().all()
            fk_count = conn.execute(text("""SELECT COUNT(*) FROM information_schema.table_constraints
                WHERE constraint_schema=:schema AND constraint_type='FOREIGN KEY'"""),
                {"schema": settings.db_name}).scalar_one()
            print(f"Tables: {len(tables)}/{EXPECTED_TABLES}")
            print(f"Foreign keys: {fk_count}/{EXPECTED_FOREIGN_KEYS} (minimum expected from specification)")
            if len(tables) != EXPECTED_TABLES:
                print("Missing table count; run: python -m scripts.init_db")
                raise SystemExit(1)
            if fk_count < EXPECTED_FOREIGN_KEYS:
                print("Some foreign keys are missing; inspect schema initialization log.")
                raise SystemExit(1)
            registry = load_specification_models(engine, settings.db_name)
            print(f"Reflected SQLAlchemy models: {len(registry.names())}/{EXPECTED_TABLES}")
            print("OK: live MySQL schema and reflected SQLAlchemy model registry are ready.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
