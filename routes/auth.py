# Auth routes | register, login, logout, password recovery

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User
from patterns.singleton import SessionManager
from patterns.chain import PasswordRecoveryChain

auth_bp = Blueprint("auth", __name__)

SECURITY_QUESTIONS = [
    "What is the name of your first pet?",
    "What is your mother's maiden name?",
    "What city were you born in?",
    "What was the make of your first car?",
    "What is the name of your childhood best friend?",
    "What is your oldest sibling's middle name?",
    "What street did you grow up on?",
    "What was the name of your elementary school?",
]


@auth_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("cars.search"))
    return render_template("index.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("cars.search"))

    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        sq1 = request.form.get("security_q1", "")
        sa1 = request.form.get("security_a1", "").strip()
        sq2 = request.form.get("security_q2", "")
        sa2 = request.form.get("security_a2", "").strip()
        sq3 = request.form.get("security_q3", "")
        sa3 = request.form.get("security_a3", "").strip()

        if not all([name, email, password, sq1, sa1, sq2, sa2, sq3, sa3]):
            flash("All fields are required.", "danger")
            return render_template("auth/register.html", questions=SECURITY_QUESTIONS)

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html", questions=SECURITY_QUESTIONS)

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("auth/register.html", questions=SECURITY_QUESTIONS)

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "danger")
            return render_template("auth/register.html", questions=SECURITY_QUESTIONS)

        user = User(
            name=name, email=email,
            security_q1=sq1, security_a1=sa1,
            security_q2=sq2, security_a2=sa2,
            security_q3=sq3, security_a3=sa3,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Account created! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", questions=SECURITY_QUESTIONS)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("cars.search"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()

        sm = SessionManager.get_instance()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f"Welcome back, {user.name}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("cars.search"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/recover", methods=["GET", "POST"])
def recover_step1():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user  = User.query.filter_by(email=email).first()

        if not user:
            flash("No account found with that email.", "danger")
            return render_template("auth/recover_step1.html")

        session["recover_user_id"] = user.id
        return redirect(url_for("auth.recover_step2"))

    return render_template("auth/recover_step1.html")


@auth_bp.route("/recover/questions", methods=["GET", "POST"])
def recover_step2():
    user_id = session.get("recover_user_id")
    if not user_id:
        return redirect(url_for("auth.recover_step1"))

    user = User.query.get(user_id)
    if not user:
        flash("Session expired. Please start over.", "danger")
        return redirect(url_for("auth.recover_step1"))

    if request.method == "POST":
        a1 = request.form.get("answer1", "")
        a2 = request.form.get("answer2", "")
        a3 = request.form.get("answer3", "")

        chain = PasswordRecoveryChain()
        if chain.verify(user, a1, a2, a3):
            session["recover_verified"] = True
            return redirect(url_for("auth.recover_step3"))
        else:
            flash("One or more answers were incorrect. Please try again.", "danger")

    return render_template("auth/recover_step2.html", user=user)


@auth_bp.route("/recover/reset", methods=["GET", "POST"])
def recover_step3():
    if not session.get("recover_verified"):
        return redirect(url_for("auth.recover_step1"))

    user_id = session.get("recover_user_id")
    user    = User.query.get(user_id)

    if request.method == "POST":
        new_password = request.form.get("password", "")
        confirm      = request.form.get("confirm_password", "")

        if len(new_password) < 6:
            flash("Password must be at least 6 characters.", "danger")
        elif new_password != confirm:
            flash("Passwords do not match.", "danger")
        else:
            user.set_password(new_password)
            db.session.commit()
            session.pop("recover_user_id", None)
            session.pop("recover_verified", None)
            flash("Password reset successfully! Please log in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/recover_step3.html")
