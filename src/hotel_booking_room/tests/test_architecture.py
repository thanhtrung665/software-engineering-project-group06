"""Kiểm tra quy tắc phụ thuộc giữa 3 tầng bằng cách quét import (AST).

Presentation -> Business -> Data Access   (chỉ được gọi xuống 1 chiều)
"""
import ast
from pathlib import Path

APP = Path(__file__).resolve().parent.parent / "app"

# tầng -> các tiền tố import bị CẤM
FORBIDDEN = {
    "presentation": ["app.data_access", "sqlalchemy", "pyodbc"],
    "business": ["app.presentation", "fastapi", "starlette", "pydantic", "sqlalchemy"],
    "data_access": ["app.presentation", "app.business", "fastapi", "starlette"],
}


def _imports(path: Path):
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            yield from (a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            yield node.module


def test_layer_dependency_rules():
    violations = []
    for layer, banned in FORBIDDEN.items():
        for f in (APP / layer).rglob("*.py"):
            for mod in _imports(f):
                # business được dùng UnitOfWork (không dùng SQLAlchemy trực tiếp)
                if any(mod == b or mod.startswith(b + ".") for b in banned):
                    violations.append(f"{f.relative_to(APP)} imports {mod}")
    assert not violations, "\n".join(violations)
