"""SQLAlchemy reflected models for every table in the 40-table specification.

The booking/hold core keeps its explicit typed models in this package. The
remaining specification entities are reflected from the authoritative MySQL
schema after scripts.init_db has run, so column definitions and FK metadata
stay identical to MySQL 8.4 instead of being duplicated in Python.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.ext.automap import automap_base

EXPECTED_TABLES = 40


class SpecificationModelRegistry:
    """Lazy registry of reflected ORM classes for the complete specification."""

    def __init__(self, engine: Engine, schema: str):
        self.schema = schema
        self.base = automap_base(metadata=MetaData())
        self.base.prepare(autoload_with=engine, schema=schema)
        self.models = self.base.classes
        table_count = len(self.base.metadata.tables)
        if table_count != EXPECTED_TABLES:
            raise RuntimeError(
                f"Expected {EXPECTED_TABLES} specification tables in '{schema}', "
                f"found {table_count}. Run scripts.init_db first."
            )

    def get(self, table_name: str) -> Any:
        """Return reflected class by its lowercase table name."""
        key = table_name.lower()
        try:
            return self.models[key]
        except KeyError as exc:
            raise KeyError(f"Unknown specification table: {table_name}") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(table.name for table in self.base.metadata.tables.values()))


def load_specification_models(engine: Engine, schema: str) -> SpecificationModelRegistry:
    """Reflect and map all 40 MySQL tables to SQLAlchemy ORM classes."""
    return SpecificationModelRegistry(engine, schema)
