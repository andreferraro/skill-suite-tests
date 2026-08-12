from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.payment import PaymentService


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


def test_serializes_concurrent_requests(service: PaymentService) -> None:
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: service.create_payment("key-concurrent", 1500), range(8)))

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
