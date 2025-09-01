from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

db = SQLAlchemy()


# ---------------- NETWORK SESSION ----------------
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

    user = db.relationship('User', backref=db.backref('network_sessions', lazy=True))
    device = db.relationship('Device', backref=db.backref('network_sessions', lazy=True))


# ---------------- USER ----------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' or 'customer'
    is_active = db.Column(db.Boolean, default=True)
    date_created = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ---------------- DEVICE ----------------
class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mac_address = db.Column(db.String(17), unique=True, nullable=False)
    device_name = db.Column(db.String(100))
    ip_address = db.Column(db.String(15))
    is_blocked = db.Column(db.Boolean, default=False)
    is_online = db.Column(db.Boolean, default=True)
    first_seen = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    user = db.relationship('User', backref=db.backref('devices', lazy=True))

    # ⚡ Helper: get profile names directly
    @property
    def profile_names(self):
        return [profile.name for profile in self.profiles]


# ---------------- ALERT ----------------
class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    alert_type = db.Column(db.String(20), default='info')  # 'info', 'warning', 'danger', 'success'
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('alerts', lazy=True))


# ---------------- FAMILY PROFILE ----------------
# Many-to-many link table
profile_devices = db.Table(
    'profile_devices',
    db.Column('profile_id', db.Integer, db.ForeignKey('family_profile.id'), primary_key=True),
    db.Column('device_id', db.Integer, db.ForeignKey('device.id'), primary_key=True)
)


class FamilyProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    enabled = db.Column(db.Boolean, default=True)
    date_created = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Many-to-many relationship with Device
    devices = db.relationship(
        'Device',
        secondary=profile_devices,
        backref=db.backref('profiles', lazy=True)
    )


# ---------------- OPTIONAL: HELPER FUNCTION ----------------
def create_admin_if_not_exists(app):
    from werkzeug.security import generate_password_hash
    with app.app_context():
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin',
                password_hash=generate_password_hash("Admin@123")
            )
            db.session.add(admin)
            db.session.commit()
