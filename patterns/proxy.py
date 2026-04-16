# PaymentProxy and RealPaymentService both implement PaymentService.
# Payment route only talks to proxy
# Proxy handles validation and logging before passing
# RealPaymentService just simulates a successful response with a fake transaction ID.

from abc import ABC, abstractmethod
from datetime import datetime


class PaymentService(ABC):

    @abstractmethod
    def pay(self, amount: float) -> dict:
        pass


class RealPaymentService(PaymentService):
    # Simulate payment

    def pay(self, amount: float) -> dict:
        txn_id = f"TXN-{int(datetime.utcnow().timestamp() * 1000)}"
        return {
            "success": True,
            "message": f"Payment of ${amount:.2f} processed successfully.",
            "transaction_id": txn_id,
        }


class PaymentProxy(PaymentService):

    def __init__(self, booking):
        self._booking = booking
        self._real_service = RealPaymentService()
        self._log: list[str] = []

    def pay(self, amount: float) -> dict:
        # Validate first, then delegate to the real service
        validation_error = self._validate(amount)
        if validation_error:
            self._log_entry(f"FAILED validation: {validation_error}")
            return {"success": False, "message": validation_error, "transaction_id": None}

        self._log_entry(f"Forwarding payment of ${amount:.2f} to RealPaymentService")

        result = self._real_service.pay(amount)

        if result["success"]:
            from extensions import db
            self._booking.status = "paid"
            db.session.commit()
            self._log_entry(
                f"Payment succeeded. TXN={result['transaction_id']}. "
                f"Booking #{self._booking.id} marked as paid."
            )
        else:
            self._log_entry(f"Payment failed: {result['message']}")

        return result

    def _validate(self, amount: float) -> str | None:
        # Returns an error string if something is wrong, or None if everything is cool
        if amount <= 0:
            return "Payment amount must be greater than zero."
        if self._booking.status == "paid":
            return "This booking has already been paid."
        if self._booking.status == "cancelled":
            return "Cannot pay for a cancelled booking."
        if self._booking.status == "pending":
            return "Booking must be confirmed by the owner before payment."
        return None

    def _log_entry(self, message: str):
        entry = f"[{datetime.utcnow().isoformat()}] PaymentProxy: {message}"
        self._log.append(entry)
        print(entry)

    def get_log(self) -> list[str]:
        return self._log
