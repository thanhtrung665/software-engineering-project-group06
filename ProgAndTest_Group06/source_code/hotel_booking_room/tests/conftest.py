from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.composition import get_uow_factory
from app.data_access.models import Base, Hotel, RoomType
from app.data_access.unit_of_work import UnitOfWork
from app.main import app


@pytest.fixture()
def session_factory():
    """SQLite in-memory: test nhanh, không cần MySQL."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as s:
        s.add(Hotel(star_rating=4, address="HCMC", hotline="1", contact_email="a@b.c"))
        s.flush()
        s.add_all([
            RoomType(hotel_id=1, room_type_code="DELUXE", area_sqm=Decimal(38), bed_type="KING",
                     max_adults=3, max_children=1, base_price=Decimal(1_800_000), selling_status="ON_SALE"),
            RoomType(hotel_id=1, room_type_code="STANDARD", area_sqm=Decimal(25), bed_type="DOUBLE",
                     max_adults=2, max_children=1, base_price=Decimal(900_000), selling_status="ON_SALE"),
            RoomType(hotel_id=1, room_type_code="OLD", area_sqm=Decimal(20), bed_type="TWIN",
                     max_adults=2, max_children=0, base_price=Decimal(500_000), selling_status="DISCONTINUED"),
        ])
        s.commit()
    return factory


@pytest.fixture()
def client(session_factory):
    app.dependency_overrides[get_uow_factory] = lambda: (lambda: UnitOfWork(session_factory))
    yield TestClient(app)
    app.dependency_overrides.clear()
