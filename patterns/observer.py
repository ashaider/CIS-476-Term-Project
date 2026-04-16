# When a car's price drops or it becomes available again, all renter watching that car get notified automatically
# CarSubject is the thing being watched (wrapper)
# WatcherObserver is the abstract observer interface.
# RenterWatcher is the concrete observer so there is one per renter watching a car.
# WatchlistManager queries the DB, builds the observers, and does notify().

from abc import ABC, abstractmethod
from models import Watchlist, Notification
from extensions import db
from datetime import datetime


class WatcherObserver(ABC):

    @abstractmethod
    def update(self, car, message: str):
        pass


class RenterWatcher(WatcherObserver):

    def __init__(self, renter_id: int, max_price: float):
        self.renter_id = renter_id
        self.max_price = max_price

    def update(self, car, message: str):
        # Write a notification row
        notification = Notification(
            user_id=self.renter_id,
            message=message,
            created_at=datetime.utcnow(),
        )
        db.session.add(notification)


class CarSubject:
    # Wraps a Car and holds the list of observers watching it

    def __init__(self, car):
        self._car = car
        self._observers: list[WatcherObserver] = []

    def attach(self, observer: WatcherObserver):
        self._observers.append(observer)

    def detach(self, observer: WatcherObserver):
        self._observers.remove(observer)

    def notify(self, message: str):
        for obs in self._observers:
            obs.update(self._car, message)


class WatchlistManager:

    @staticmethod
    def notify_watchers(car):
        # Find everyone watching this car
        entries = Watchlist.query.filter_by(car_id=car.id).all()
        if not entries:
            return

        subject = CarSubject(car)

        for entry in entries:
            # Only attach watchers whose budget covers the current price
            if car.price_per_day <= entry.max_price and car.is_available:
                watcher = RenterWatcher(entry.renter_id, entry.max_price)
                subject.attach(watcher)

        if not subject._observers:
            return

        message = (
            f"Good news! '{car.year} {car.make} {car.model}' in {car.location} "
            f"is now available at ${car.price_per_day:.2f}/day - "
            f"within your watch budget!"
        )

        subject.notify(message)
        db.session.commit()
