# Booking routes | create, confirm, cancel bookings

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Car, Booking, User
from patterns.mediator import booking_colleague
from datetime import date

booking_bp = Blueprint("booking", __name__)


def _dates_overlap(start1, end1, start2, end2) -> bool:
    return start1 <= end2 and end1 >= start2


@booking_bp.route("/cars/<int:car_id>/book", methods=["GET", "POST"])
@login_required
def book_car(car_id):
    car = Car.query.get_or_404(car_id)

    if car.owner_id == current_user.id:
        flash("You cannot book your own car.", "warning")
        return redirect(url_for("cars.car_detail", car_id=car_id))

    if not car.is_available:
        flash("This car is currently not available.", "warning")
        return redirect(url_for("cars.car_detail", car_id=car_id))

    if request.method == "POST":
        start_str = request.form.get("start_date", "")
        end_str   = request.form.get("end_date", "")

        try:
            start_date = date.fromisoformat(start_str)
            end_date   = date.fromisoformat(end_str)
        except ValueError:
            flash("Invalid dates provided.", "danger")
            return render_template("booking/book.html", car=car)

        if start_date < date.today():
            flash("Start date cannot be in the past.", "danger")
            return render_template("booking/book.html", car=car)

        if end_date <= start_date:
            flash("End date must be after start date.", "danger")
            return render_template("booking/book.html", car=car)

        if start_date < car.available_from or end_date > car.available_to:
            flash(
                f"Car is only available from {car.available_from} to {car.available_to}.",
                "danger"
            )
            return render_template("booking/book.html", car=car)

        # Check for date conflicts with existing confirmed/paid bookings
        for existing in car.bookings:
            if existing.status in ("confirmed", "paid"):
                if _dates_overlap(start_date, end_date, existing.start_date, existing.end_date):
                    flash(
                        "Those dates overlap with an existing booking. Please choose different dates.",
                        "danger"
                    )
                    return render_template("booking/book.html", car=car)

        num_days    = (end_date - start_date).days
        total_price = num_days * car.price_per_day

        booking = Booking(
            car_id=car.id,
            renter_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            total_price=total_price,
            status="pending",
        )
        db.session.add(booking)
        db.session.flush()

        owner = User.query.get(car.owner_id)
        booking_colleague.booking_created(booking, car, current_user, owner)

        db.session.commit()
        flash(
            f"Booking request submitted! Total: ${total_price:.2f} for {num_days} day(s).",
            "success"
        )
        return redirect(url_for("booking.my_bookings"))

    return render_template("booking/book.html", car=car)


@booking_bp.route("/my-bookings")
@login_required
def my_bookings():
    bookings = (
        Booking.query
        .filter_by(renter_id=current_user.id)
        .order_by(Booking.created_at.desc())
        .all()
    )
    return render_template("booking/my_bookings.html", bookings=bookings)


@booking_bp.route("/owner/bookings")
@login_required
def owner_bookings():
    owned_car_ids = [car.id for car in current_user.cars]
    bookings = (
        Booking.query
        .filter(Booking.car_id.in_(owned_car_ids))
        .order_by(Booking.created_at.desc())
        .all()
    )
    return render_template("booking/owner_bookings.html", bookings=bookings)


@booking_bp.route("/bookings/<int:booking_id>/confirm", methods=["POST"])
@login_required
def confirm_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    car     = Car.query.get(booking.car_id)

    if car.owner_id != current_user.id:
        flash("Permission denied.", "danger")
        return redirect(url_for("booking.owner_bookings"))

    if booking.status != "pending":
        flash("This booking is not in a pending state.", "warning")
        return redirect(url_for("booking.owner_bookings"))

    booking.status = "confirmed"
    renter = User.query.get(booking.renter_id)
    booking_colleague.booking_confirmed(booking, car, renter, current_user)

    db.session.commit()
    flash(f"Booking confirmed for {renter.name}.", "success")
    return redirect(url_for("booking.owner_bookings"))


@booking_bp.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    car     = Car.query.get(booking.car_id)
    renter  = User.query.get(booking.renter_id)
    owner   = User.query.get(car.owner_id)

    if current_user.id not in (booking.renter_id, car.owner_id):
        flash("Permission denied.", "danger")
        return redirect(url_for("booking.my_bookings"))

    if booking.status == "paid":
        flash("Paid bookings cannot be cancelled.", "warning")
        return redirect(url_for("booking.my_bookings"))

    booking.status = "cancelled"
    booking_colleague.booking_cancelled(booking, car, renter, owner)

    db.session.commit()
    flash("Booking cancelled.", "info")

    if current_user.id == booking.renter_id:
        return redirect(url_for("booking.my_bookings"))
    return redirect(url_for("booking.owner_bookings"))
