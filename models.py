from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

db = SQLAlchemy()












class NetworkSession(db.Model):
    """
    NetworkSession model to track user/device network activity.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    ip_address = db.Column(db.String(15))
    mac_address = db.Column(db.String(17))
    session_start = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    session_end = db.Column(db.DateTime, nullable=True)  # None if session is ongoing

    # Relationships
    user = db.relationship('User', backref=db.backref('network_sessions', lazy=True))
    device = db.relationship('Device', backref=db.backref('network_sessions', lazy=True))


# ---------------- EXISTING MODELS ----------------
class User(UserMixin, db.Model):
    """
    User model for authentication and role-based access.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)  # 'admin' or 'customer'
    is_active = db.Column(db.Boolean, default=True)
    date_created = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def set_password(self, password):
        """Hashes the given password and stores it."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Checks if the given password matches the stored hash."""
        return check_password_hash(self.password_hash, password)


class Device(db.Model):
    """
    Device model to store information about connected network devices.
    """
    id = db.Column(db.Integer, primary_key=True)
    mac_address = db.Column(db.String(17), unique=True, nullable=False)
    device_name = db.Column(db.String(100))
    ip_address = db.Column(db.String(15))
    is_blocked = db.Column(db.Boolean, default=False)
    is_online = db.Column(db.Boolean, default=True)
    first_seen = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationship to User
    user = db.relationship('User', backref=db.backref('devices', lazy=True))


class Alert(db.Model):
    """
    Alert model for system notifications (e.g., new device, device disconnected).
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    alert_type = db.Column(db.String(20))  # 'info', 'warning', 'danger', 'success'
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationship to User
    user = db.relationship('User', backref=db.backref('alerts', lazy=True))


# ---------------- NEW MODELS FOR FAMILY PROFILES ----------------
class FamilyProfile(db.Model):
    """
    Family Profile model for grouping devices.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    enabled = db.Column(db.Boolean, default=True)  # True = Internet enabled
    date_created = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to link devices via ProfileDevice
    devices = db.relationship('ProfileDevice', backref='profile', lazy=True)


class ProfileDevice(db.Model):
    """
    Association table to link devices to family profiles (many-to-many).
    """
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('family_profile.id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)

    # Relationship to access the Device object
    device = db.relationship('Device', backref=db.backref('profiles', lazy=True))
