# Watchlist routes | watch/unwatch a car, mark notifications as read

from flask import Blueprint, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Car, Watchlist

watchlist_bp = Blueprint("watchlist", __name__)


@watchlist_bp.route("/cars/<int:car_id>/watch", methods=["POST"])
@login_required
def watch_car(car_id):
    car = Car.query.get_or_404(car_id)

    if car.owner_id == current_user.id:
        flash("You cannot watch your own listing.", "warning")
        return redirect(url_for("cars.car_detail", car_id=car_id))

    max_price = request.form.get("max_price", type=float)
    if not max_price or max_price <= 0:
        flash("Please enter a valid max price.", "danger")
        return redirect(url_for("cars.car_detail", car_id=car_id))

    # Update the existing watch if one exists, otherwise create a new one
    existing = Watchlist.query.filter_by(
        renter_id=current_user.id, car_id=car_id
    ).first()

    if existing:
        existing.max_price = max_price
        flash(f"Watch updated - you'll be notified if the price drops to ${max_price:.2f}/day or below.", "info")
    else:
        watch = Watchlist(renter_id=current_user.id, car_id=car_id, max_price=max_price)
        db.session.add(watch)
        flash(f"Watching this car! You'll be notified if the price drops to ${max_price:.2f}/day or below.", "success")

    db.session.commit()
    return redirect(url_for("cars.car_detail", car_id=car_id))


@watchlist_bp.route("/cars/<int:car_id>/unwatch", methods=["POST"])
@login_required
def unwatch_car(car_id):
    watch = Watchlist.query.filter_by(
        renter_id=current_user.id, car_id=car_id
    ).first()

    if watch:
        db.session.delete(watch)
        db.session.commit()
        flash("Removed from your watchlist.", "info")

    return redirect(url_for("cars.car_detail", car_id=car_id))


@watchlist_bp.route("/notifications/mark-read", methods=["POST"])
@login_required
def mark_notifications_read():
    from models import Notification
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return redirect(request.referrer or url_for("cars.search"))
