# When a booking is created, a payment is made, a message is sent, etc, the relevant Colleague class fires mediator.notify() and the mediator handles creating whatever needs to exist.

from abc import ABC, abstractmethod
from models import Notification, Message
from extensions import db
from datetime import datetime


class BaseMediator(ABC):

    @abstractmethod
    def notify(self, colleague: str, event: str, **kwargs):
        pass


class MediatorColleague:
    # Base class for all colleagues - just holds a reference to the mediator

    def __init__(self, mediator: BaseMediator):
        self._mediator = mediator


class BookingColleague(MediatorColleague):

    def booking_created(self, booking, car, renter, owner):
        self._mediator.notify(
            "booking", "booking_created",
            booking=booking, car=car, renter=renter, owner=owner
        )

    def booking_confirmed(self, booking, car, renter, owner):
        self._mediator.notify(
            "booking", "booking_confirmed",
            booking=booking, car=car, renter=renter, owner=owner
        )

    def booking_cancelled(self, booking, car, renter, owner):
        self._mediator.notify(
            "booking", "booking_cancelled",
            booking=booking, car=car, renter=renter, owner=owner
        )


class PaymentColleague(MediatorColleague):

    def payment_made(self, booking, car, renter, owner, amount):
        self._mediator.notify(
            "payment", "payment_made",
            booking=booking, car=car, renter=renter, owner=owner, amount=amount
        )


class MessageColleague(MediatorColleague):

    def message_sent(self, sender, receiver, body):
        self._mediator.notify(
            "message", "message_sent",
            sender=sender, receiver=receiver, body=body
        )


class NotificationMediator(BaseMediator):

    def notify(self, colleague: str, event: str, **kwargs):
        # Look up the right handler by event name and call it
        handler = getattr(self, f"_handle_{event}", None)
        if handler:
            handler(**kwargs)

    def _handle_booking_created(self, booking, car, renter, owner):
        # Notify the owner someone requested their car
        self._add_notification(
            user_id=owner.id,
            message=(
                f"New booking request from {renter.name} for your "
                f"{car.year} {car.make} {car.model} "
                f"({booking.start_date} to {booking.end_date})."
            ),
        )
        # Also let the renter know it went through
        self._add_notification(
            user_id=renter.id,
            message=(
                f"Your booking request for {car.year} {car.make} {car.model} "
                f"({booking.start_date} to {booking.end_date}) has been submitted."
            ),
        )

    def _handle_booking_confirmed(self, booking, car, renter, owner):
        self._add_notification(
            user_id=renter.id,
            message=(
                f"Your booking for {car.year} {car.make} {car.model} "
                f"({booking.start_date} to {booking.end_date}) has been confirmed! "
                f"Total: ${booking.total_price:.2f}."
            ),
        )

    def _handle_booking_cancelled(self, booking, car, renter, owner):
        for uid, who in [(renter.id, "Your"), (owner.id, f"{renter.name}'s")]:
            self._add_notification(
                user_id=uid,
                message=(
                    f"{who} booking for {car.year} {car.make} {car.model} "
                    f"({booking.start_date} to {booking.end_date}) has been cancelled."
                ),
            )

    def _handle_payment_made(self, booking, car, renter, owner, amount):
        self._add_notification(
            user_id=renter.id,
            message=f"Payment of ${amount:.2f} confirmed for {car.year} {car.make} {car.model}.",
        )
        self._add_notification(
            user_id=owner.id,
            message=(
                f"{renter.name} has paid ${amount:.2f} for "
                f"{car.year} {car.make} {car.model} "
                f"({booking.start_date} to {booking.end_date})."
            ),
        )

    def _handle_message_sent(self, sender, receiver, body):
        msg = Message(
            sender_id=sender.id,
            receiver_id=receiver.id,
            body=body,
            created_at=datetime.utcnow(),
        )
        db.session.add(msg)
        preview = body[:60] + ("..." if len(body) > 60 else "")
        self._add_notification(
            user_id=receiver.id,
            message=f"New message from {sender.name}: \"{preview}\"",
        )

    def _add_notification(self, user_id: int, message: str):
        notif = Notification(
            user_id=user_id,
            message=message,
            created_at=datetime.utcnow(),
        )
        db.session.add(notif)


# Shared instances used by the route blueprints
mediator = NotificationMediator()
booking_colleague = BookingColleague(mediator)
payment_colleague = PaymentColleague(mediator)
message_colleague = MessageColleague(mediator)
