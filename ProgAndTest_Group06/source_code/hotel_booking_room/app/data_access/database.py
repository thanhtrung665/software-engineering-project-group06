"""Engine + session factory (MySQL/InnoDB qua PyMySQL)."""
from functools import lru_cache

from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL, Engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

# InnoDB lock wait timeout được cấu hình theo giây trên từng connection.
LOCK_WAIT_TIMEOUT_SECONDS = 10


def build_engine(url: URL | str) -> Engine:
    """Tạo engine MySQL; READ COMMITTED + timeout khóa hữu hạn."""
    engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=1800,  # MySQL tự ngắt kết nối nhàn rỗi (wait_timeout)
        isolation_level="READ COMMITTED",
        connect_args={"charset": "utf8mb4"},
    )

    @event.listens_for(engine, "connect")
    def _set_lock_timeout(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        try:
            cur.execute(f"SET SESSION innodb_lock_wait_timeout = {LOCK_WAIT_TIMEOUT_SECONDS}")
        finally:
            cur.close()

    return engine


@lru_cache
def get_engine() -> Engine:
    return build_engine(get_settings().database_url)


@lru_cache
def get_session_factory() -> sessionmaker:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)
