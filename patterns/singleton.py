# Only one SessionManager instance ever gets created. Calling get_instance()
# from anywhere will always returns that same object.
# Wraps Flask-Login for check session state instead of importing current_user everywhere.

from flask_login import current_user
from models import Notification


class SessionManager:

    _instance = None

    def __new__(cls):
        # If no instance exists yet, create one and cache it
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def get_instance():
        return SessionManager()

    def get_current_user(self):
        return current_user

    def is_authenticated(self):
        return current_user.is_authenticated

    def unread_notification_count(self):
        # Used by the nav bar to show the badge number on the bell icon
        if not self.is_authenticated():
            return 0
        return Notification.query.filter_by(
            user_id=current_user.id, is_read=False
        ).count()

    def unread_message_count(self):
        from models import Message
        if not self.is_authenticated():
            return 0
        return Message.query.filter_by(
            receiver_id=current_user.id, is_read=False
        ).count()
