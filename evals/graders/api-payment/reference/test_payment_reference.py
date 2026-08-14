from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from sqlite3 import Connection
from threading import Barrier
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.payment import PaymentService


class CoordinatedConnection:
    """Make deferred readers reach the write boundary together."""

    def __init__(self, connection: Connection, readers: Barrier):
        self._connection = connection
        self._readers = readers
        self._deferred = False

    def execute(self, sql: str, *args: Any, **kwargs: Any) -> Any:
        cursor = self._connection.execute(sql, *args, **kwargs)
        normalized = " ".join(sql.upper().split())
        if normalized == "BEGIN DEFERRED":
            self._deferred = True
        elif self._deferred and normalized.startswith(
            "SELECT ID, AMOUNT FROM PAYMENTS"
        ):
            self._readers.wait(timeout=5)
        return cursor

    def __getattr__(self, name: str) -> Any:
        return getattr(self._connection, name)

    def __enter__(self) -> "CoordinatedConnection":
        self._connection.__enter__()
        return self

    def __exit__(self, *args: Any) -> Any:
        return self._connection.__exit__(*args)


@pytest.fixture
def service(tmp_path: Path) -> PaymentService:
    return PaymentService(tmp_path / "payments.db")


def test_returns_stable_result_for_same_idempotency_key(service: PaymentService) -> None:
    first = service.create_payment("key-1", 1000)
    second = service.create_payment("key-1", 1000)

    assert first.id == second.id
    assert first.created is True
    assert second.created is False
    assert service.count_payments() == 1


def test_serializes_concurrent_requests(
    service: PaymentService, monkeypatch: pytest.MonkeyPatch
) -> None:
    workers = 8
    readers = Barrier(workers)
    connect = service._connect
    monkeypatch.setattr(
        service,
        "_connect",
        lambda: CoordinatedConnection(connect(), readers),
    )

    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(
            executor.map(
                lambda _: service.create_payment("key-concurrent", 1500),
                range(workers),
            )
        )

    assert len({payment.id for payment in results}) == 1
    assert sum(payment.created for payment in results) == 1
    assert service.count_payments() == 1


def test_rejects_zero_amount(service: PaymentService) -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        service.create_payment("key-zero", 0)

    assert service.count_payments() == 0


def test_rolls_back_after_insert_failure(service: PaymentService) -> None:
    with pytest.raises(RuntimeError, match="downstream"):
        service.create_payment("key-failure", 2000, fail_after_insert=True)

    assert service.count_payments() == 0


def test_fastapi_preserves_idempotency_and_validates_input(service: PaymentService) -> None:
    client = TestClient(create_app(service))
    headers = {"Idempotency-Key": "http-key"}

    first = client.post("/payments", headers=headers, json={"amount": 2500})
    second = client.post("/payments", headers=headers, json={"amount": 2500})
    invalid = client.post("/payments", headers={"Idempotency-Key": "zero"}, json={"amount": 0})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["created"] is True
    assert second.json()["created"] is False
    assert invalid.status_code == 422
