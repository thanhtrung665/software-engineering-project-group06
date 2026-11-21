"""Kiểm tra quy tắc phụ thuộc giữa 3 tầng bằng cách quét import (AST).

Presentation -> Business -> Data Access   (chỉ được gọi xuống 1 chiều)
"""
import ast
from pathlib import Path

APP = Path(__file__).resolve().parent.parent / "app"

# tầng -> các tiền tố import bị CẤM
FORBIDDEN = {
    "presentation": ["app.data_access", "sqlalchemy", "pymysql", "mysql", "requests"],
    "business": ["app.presentation", "fastapi", "starlette", "pydantic", "sqlalchemy", "pymysql", "mysql",
                 "requests"],
    "data_access": ["app.presentation", "app.business", "fastapi", "starlette"],
}

# Mọi mã nguồn trong app/ phải thuộc 1 trong 3 tầng, hoặc là phần dùng chung / điểm khởi động.
ALLOWED_TOP_LEVEL = {"presentation", "business", "data_access", "core",
                     "__init__.py", "main.py", "composition.py"}


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


def test_every_module_belongs_to_a_layer():
    """Chặn việc thêm module 'ngoài kiến trúc' (vd thư mục app/payments/ cũ) mà test phụ thuộc ở trên không quét tới."""
    stray = sorted(p.name for p in APP.iterdir() if p.name != "__pycache__" and p.name not in ALLOWED_TOP_LEVEL)
    assert not stray, f"Đặt các module này vào presentation/business/data_access: {stray}"
