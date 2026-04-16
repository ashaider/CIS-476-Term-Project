# Messaging routes | inbox, conversation threads, sending messages

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import User, Message
from patterns.mediator import message_colleague

messages_bp = Blueprint("messages", __name__)


@messages_bp.route("/messages")
@login_required
def inbox():
    msgs = (
        Message.query
        .filter_by(receiver_id=current_user.id)
        .order_by(Message.created_at.desc())
        .all()
    )
    return render_template("messages/inbox.html", messages=msgs)


@messages_bp.route("/messages/<int:other_id>")
@login_required
def conversation(other_id):
    other = User.query.get_or_404(other_id)

    thread = (
        Message.query
        .filter(
            ((Message.sender_id   == current_user.id) & (Message.receiver_id == other_id)) |
            ((Message.sender_id   == other_id)         & (Message.receiver_id == current_user.id))
        )
        .order_by(Message.created_at.asc())
        .all()
    )

    for msg in thread:
        if msg.receiver_id == current_user.id and not msg.is_read:
            msg.is_read = True
    db.session.commit()

    return render_template("messages/conversation.html", other=other, thread=thread)


@messages_bp.route("/messages/<int:other_id>/send", methods=["POST"])
@login_required
def send_message(other_id):
    other = User.query.get_or_404(other_id)
    body  = request.form.get("body", "").strip()

    if not body:
        flash("Message cannot be empty.", "warning")
        return redirect(url_for("messages.conversation", other_id=other_id))

    message_colleague.message_sent(current_user, other, body)
    db.session.commit()

    return redirect(url_for("messages.conversation", other_id=other_id))


@messages_bp.route("/messages/new/<int:other_id>", methods=["GET"])
@login_required
def new_conversation(other_id):
    other = User.query.get_or_404(other_id)
    return redirect(url_for("messages.conversation", other_id=other_id))
