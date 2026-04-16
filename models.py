# Database models for DriveShare.
# Tables: User, Car, Booking, Message, Notification, Watchlist

from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User(UserMixin, db.Model):
    # A user can be both an owner and a renter
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name          = db.Column(db.String(100), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # Security questions used for password recovery
    security_q1 = db.Column(db.String(200), nullable=False)
    security_a1 = db.Column(db.String(200), nullable=False)
    security_q2 = db.Column(db.String(200), nullable=False)
    security_a2 = db.Column(db.String(200), nullable=False)
    security_q3 = db.Column(db.String(200), nullable=False)
    security_a3 = db.Column(db.String(200), nullable=False)

    cars          = db.relationship("Car",          backref="owner",    lazy=True)
    bookings      = db.relationship("Booking",      backref="renter",   lazy=True)
    sent_messages = db.relationship("Message",      foreign_keys="Message.sender_id",   backref="sender",   lazy=True)
    recv_messages = db.relationship("Message",      foreign_keys="Message.receiver_id", backref="receiver", lazy=True)
    notifications = db.relationship("Notification", backref="user",     lazy=True)
    watchlist     = db.relationship("Watchlist",    backref="renter",   lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


class Car(db.Model):
    __tablename__ = "cars"

    id       = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    make           = db.Column(db.String(50),  nullable=False)
    model          = db.Column(db.String(50),  nullable=False)
    year           = db.Column(db.Integer,     nullable=False)
    price_per_day  = db.Column(db.Float,       nullable=False)
    location       = db.Column(db.String(200), nullable=False)
    available_from = db.Column(db.Date,        nullable=False)
    available_to   = db.Column(db.Date,        nullable=False)

    # Optional fields - set via the Builder pattern
    mileage      = db.Column(db.String(50),  default="Unknown")
    transmission = db.Column(db.String(20),  default="Automatic")
    seats        = db.Column(db.Integer,     default=5)
    description  = db.Column(db.Text,        default="")
    image_url    = db.Column(db.String(300), default="")
    is_available = db.Column(db.Boolean,     default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings  = db.relationship("Booking",   backref="car", lazy=True)
    watchlist = db.relationship("Watchlist", backref="car", lazy=True)

    def __repr__(self):
        return f"<Car {self.year} {self.make} {self.model}>"


class Booking(db.Model):
    # Status can be pending, confirmed, paid,or cancelled
    __tablename__ = "bookings"

    id          = db.Column(db.Integer, primary_key=True)
    car_id      = db.Column(db.Integer, db.ForeignKey("cars.id"),  nullable=False)
    renter_id   = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    start_date  = db.Column(db.Date,    nullable=False)
    end_date    = db.Column(db.Date,    nullable=False)
    total_price = db.Column(db.Float,   nullable=False)
    status      = db.Column(db.String(20), default="pending")
    created_at  = db.Column(db.DateTime,   default=datetime.utcnow)

    def __repr__(self):
        return f"<Booking car={self.car_id} renter={self.renter_id} {self.start_date} to {self.end_date}>"


class Message(db.Model):
    __tablename__ = "messages"

    id          = db.Column(db.Integer, primary_key=True)
    sender_id   = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body        = db.Column(db.Text,    nullable=False)
    is_read     = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Message from={self.sender_id} to={self.receiver_id}>"


class Notification(db.Model):
    __tablename__ = "notifications"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message    = db.Column(db.String(300), nullable=False)
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Notification user={self.user_id} read={self.is_read}>"


class Watchlist(db.Model):
    # Renter watches a car and sets a max price and then are notified when price drops to/below it
    __tablename__ = "watchlist"

    id        = db.Column(db.Integer, primary_key=True)
    renter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    car_id    = db.Column(db.Integer, db.ForeignKey("cars.id"),  nullable=False)
    max_price = db.Column(db.Float,   nullable=False)

    def __repr__(self):
        return f"<Watchlist renter={self.renter_id} car={self.car_id} max=${self.max_price}>"
