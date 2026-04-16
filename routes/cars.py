# Car listing and search routes

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Car, Booking
from patterns.builder import build_car_from_form
from patterns.observer import WatchlistManager
from datetime import date

cars_bp = Blueprint("cars", __name__)


@cars_bp.route("/search")
@login_required
def search():
    query     = request.args.get("q", "").strip()
    from_str  = request.args.get("from_date", "")
    to_str    = request.args.get("to_date", "")
    max_price = request.args.get("max_price", type=float)

    cars_query = Car.query.filter_by(is_available=True)

    if query:
        cars_query = cars_query.filter(
            Car.location.ilike(f"%{query}%") |
            Car.make.ilike(f"%{query}%") |
            Car.model.ilike(f"%{query}%")
        )

    if from_str and to_str:
        try:
            from_date = date.fromisoformat(from_str)
            to_date   = date.fromisoformat(to_str)
            # Car has to cover the full requested range
            cars_query = cars_query.filter(
                Car.available_from <= from_date,
                Car.available_to   >= to_date,
            )
        except ValueError:
            flash("Invalid date format.", "warning")

    if max_price:
        cars_query = cars_query.filter(Car.price_per_day <= max_price)

    # Don't show the user their own cars in search results
    cars_query = cars_query.filter(Car.owner_id != current_user.id)

    cars = cars_query.order_by(Car.created_at.desc()).all()

    return render_template("cars/search.html", cars=cars,
                           query=query, from_str=from_str,
                           to_str=to_str, max_price=max_price)


@cars_bp.route("/cars/<int:car_id>")
@login_required
def car_detail(car_id):
    car = Car.query.get_or_404(car_id)
    booked_ranges = [
        (b.start_date, b.end_date)
        for b in car.bookings
        if b.status in ("confirmed", "paid")
    ]
    return render_template("cars/detail.html", car=car, booked_ranges=booked_ranges)


@cars_bp.route("/my-listings")
@login_required
def my_listings():
    cars = Car.query.filter_by(owner_id=current_user.id).order_by(Car.created_at.desc()).all()
    return render_template("cars/my_listings.html", cars=cars)


@cars_bp.route("/cars/add", methods=["GET", "POST"])
@login_required
def add_car():
    if request.method == "POST":
        try:
            car_data = build_car_from_form(current_user.id, request.form)
            car = Car(**car_data)
            db.session.add(car)
            db.session.commit()
            flash("Car listed successfully!", "success")
            return redirect(url_for("cars.my_listings"))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template("cars/add_car.html")


@cars_bp.route("/cars/<int:car_id>/edit", methods=["GET", "POST"])
@login_required
def edit_car(car_id):
    car = Car.query.get_or_404(car_id)

    if car.owner_id != current_user.id:
        flash("You don't have permission to edit this listing.", "danger")
        return redirect(url_for("cars.my_listings"))

    if request.method == "POST":
        old_price     = car.price_per_day
        old_available = car.is_available

        try:
            car_data = build_car_from_form(current_user.id, request.form)
            for key, value in car_data.items():
                if key != "owner_id":
                    setattr(car, key, value)

            db.session.commit()

            # If the price dropped or the car just became available, notify watchers
            price_dropped    = car.price_per_day < old_price
            became_available = car.is_available and not old_available

            if price_dropped or became_available:
                WatchlistManager.notify_watchers(car)

            flash("Listing updated successfully!", "success")
            return redirect(url_for("cars.my_listings"))

        except ValueError as e:
            flash(str(e), "danger")

    return render_template("cars/edit_car.html", car=car)


@cars_bp.route("/cars/<int:car_id>/toggle", methods=["POST"])
@login_required
def toggle_availability(car_id):
    car = Car.query.get_or_404(car_id)

    if car.owner_id != current_user.id:
        flash("Permission denied.", "danger")
        return redirect(url_for("cars.my_listings"))

    old_available    = car.is_available
    car.is_available = not car.is_available
    db.session.commit()

    if car.is_available and not old_available:
        WatchlistManager.notify_watchers(car)

    status = "available" if car.is_available else "unavailable"
    flash(f"Listing marked as {status}.", "info")
    return redirect(url_for("cars.my_listings"))


@cars_bp.route("/cars/<int:car_id>/delete", methods=["POST"])
@login_required
def delete_car(car_id):
    car = Car.query.get_or_404(car_id)

    if car.owner_id != current_user.id:
        flash("Permission denied.", "danger")
        return redirect(url_for("cars.my_listings"))

    # Cancel any open bookings before removing the listing
    for booking in car.bookings:
        if booking.status in ("pending", "confirmed"):
            booking.status = "cancelled"

    db.session.delete(car)
    db.session.commit()
    flash("Listing deleted.", "info")
    return redirect(url_for("cars.my_listings"))
