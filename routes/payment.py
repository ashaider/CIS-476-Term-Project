# Payment route | runs the booking through the proxy before charging

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Booking, Car, User
from patterns.proxy import PaymentProxy
from patterns.mediator import payment_colleague
from extensions import db

payment_bp = Blueprint("payment", __name__)


@payment_bp.route("/bookings/<int:booking_id>/pay", methods=["GET", "POST"])
@login_required
def pay(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if booking.renter_id != current_user.id:
        flash("Permission denied.", "danger")
        return redirect(url_for("booking.my_bookings"))

    car   = Car.query.get(booking.car_id)
    owner = User.query.get(car.owner_id)

    if request.method == "POST":
        # Proxy validates the booking then delegates to RealPaymentService
        proxy  = PaymentProxy(booking)
        result = proxy.pay(booking.total_price)

        if result["success"]:
            payment_colleague.payment_made(
                booking, car, current_user, owner, booking.total_price
            )
            db.session.commit()
            flash(
                f"Payment of ${booking.total_price:.2f} successful! "
                f"Transaction ID: {result['transaction_id']}",
                "success"
            )
            return redirect(url_for("booking.my_bookings"))
        else:
            flash(f"Payment failed: {result['message']}", "danger")

    return render_template("payment/pay.html", booking=booking, car=car)
