from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True)
class Payment:
    id: str
    idempotency_key: str
    amount: int
    created: bool


class PaymentService:
    def __init__(self, database: Path):
        self.database = database
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database, timeout=5, check_same_thread=False)
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS payments (
                    id TEXT PRIMARY KEY,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    amount INTEGER NOT NULL,
                    status TEXT NOT NULL
                )
                """
            )

    def create_payment(
        self,
        idempotency_key: str,
        amount: int,
        *,
        fail_after_insert: bool = False,
    ) -> Payment:
        if not idempotency_key.strip():
            raise ValueError("idempotency_key is required")
        if amount <= 0:
            raise ValueError("amount must be greater than zero")

        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT id, amount FROM payments WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if existing:
                connection.commit()
                return Payment(id=existing[0], idempotency_key=idempotency_key, amount=existing[1], created=False)

            payment_id = str(uuid4())
            connection.execute(
                "INSERT INTO payments (id, idempotency_key, amount, status) VALUES (?, ?, ?, ?)",
                (payment_id, idempotency_key, amount, "created"),
            )
            if fail_after_insert:
                raise RuntimeError("simulated downstream failure")
            connection.commit()
            return Payment(id=payment_id, idempotency_key=idempotency_key, amount=amount, created=True)
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def count_payments(self) -> int:
        with self._connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM payments").fetchone()[0])
