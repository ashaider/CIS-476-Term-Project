# Main Flask app
# Sets up the config and creates the database tables on first run

from flask import Flask
from extensions import db, login_manager
from models import User
import os


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "driveshare-cis476-secret"

    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///" + os.path.join(basedir, "driveshare.db")
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes.auth     import auth_bp
    from routes.cars     import cars_bp
    from routes.booking  import booking_bp
    from routes.messages import messages_bp
    from routes.payment  import payment_bp
    from routes.watchlist import watchlist_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(cars_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(watchlist_bp)

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
