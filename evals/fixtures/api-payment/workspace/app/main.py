from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .payment import PaymentService


class PaymentRequest(BaseModel):
    amount: int = Field(gt=0)


def create_app(service: PaymentService) -> FastAPI:
    application = FastAPI()

    @application.post("/payments")
    def create_payment(payload: PaymentRequest, idempotency_key: str = Header(alias="Idempotency-Key")):
        try:
            payment = service.create_payment(idempotency_key, payload.amount)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return {
            "id": payment.id,
            "amount": payment.amount,
            "created": payment.created,
        }

    return application


app = create_app(PaymentService(Path("payments.db")))
