import os
from datetime import datetime, timezone
from functools import wraps
import json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

# --- Database & Models ---
from models import db, User, Device, Alert 

# --- Forms ---
from forms import LoginForm, RegistrationForm, CustomerForm, AlertForm

# --- RouterManager Integration ---

from router_manager import RouterManager
router_manager = RouterManager()




# --- Flask App Config ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# --- User Loader ---
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- Role-Based Access Control ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def customer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'customer':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---
@app.route("/")
@app.route("/index")
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        user.password_hash = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash('Logged in successfully.', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'customer':
        return redirect(url_for('customer_dashboard'))
    else:
        flash('Invalid user role.', 'danger')
        return redirect(url_for('logout'))

# --- Admin Dashboard ---
@app.route("/admin/dashboard")
@login_required
@admin_required
def admin_dashboard():
    router_devices_data = []
    try:
        router_devices_data = router_manager.get_connected_devices()
    except Exception as e:
        print(f"[RouterManager] Error fetching devices: {e}")

    if router_devices_data:
        router_macs = {d['mac_address'] for d in router_devices_data}
        all_db_devices = Device.query.all()
        for db_device in all_db_devices:
            if db_device.mac_address not in router_macs:
                db_device.last_seen = None

        for r_dev in router_devices_data:
            device = Device.query.filter_by(mac_address=r_dev['mac_address']).first()
            if device:
                device.is_blocked = r_dev['is_blocked_on_router']
                device.ip_address = r_dev['ipv4']
                device.last_seen = datetime.now(timezone.utc)
            else:
                new_device = Device(
                    mac_address=r_dev['mac_address'],
                    device_name=r_dev['name'],
                    ip_address=r_dev['ipv4'],
                    is_blocked=r_dev['is_blocked_on_router'],
                    first_seen=datetime.now(timezone.utc),
                    last_seen=datetime.now(timezone.utc)
                )
                db.session.add(new_device)
        db.session.commit()

    total_devices = Device.query.count()
    online_devices_count = sum(1 for d in Device.query.all() if d.last_seen and (datetime.now(timezone.utc) - d.last_seen.replace(tzinfo=timezone.utc)).total_seconds() < 60 and not d.is_blocked)
    blocked_devices = Device.query.filter_by(is_blocked=True).count()
    recent_alerts = Alert.query.order_by(Alert.created_at.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
                           total_devices=total_devices,
                           online_devices=online_devices_count,
                           blocked_devices=blocked_devices,
                           recent_alerts=recent_alerts)

# --- Customer Dashboard ---
@app.route("/customer/dashboard")
@login_required
@customer_required
def customer_dashboard():
    recent_alerts = Alert.query.filter_by(user_id=current_user.id).order_by(Alert.created_at.desc()).limit(5).all()
    return render_template('customer/dashboard.html', recent_alerts=recent_alerts)

# --- Admin Devices ---
@app.route("/admin/devices")
@login_required
@admin_required
def admin_devices():
    devices = Device.query.all()
    return render_template('admin/devices.html', devices=devices)

# --- Admin Alerts ---
@app.route("/admin/alerts", methods=['GET', 'POST'])
@login_required
@admin_required
def admin_alerts():
    form = AlertForm()
    users_for_select = User.query.filter_by(role='customer').all()
    form.customer_id.choices = [(0, 'All Customers')] + [(user.id, user.username) for user in users_for_select]

    if form.validate_on_submit():
        if form.send_to.data == 'all':
            for user in User.query.filter_by(role='customer').all():
                db.session.add(Alert(title=form.title.data, message=form.message.data, alert_type=form.alert_type.data, user_id=user.id))
            flash('Alert sent to all customers!', 'success')
        elif form.send_to.data == 'specific':
            user_id = form.customer_id.data
            user = User.query.get(user_id)
            if user:
                db.session.add(Alert(title=form.title.data, message=form.message.data, alert_type=form.alert_type.data, user_id=user.id))
                flash(f'Alert sent to {user.username}!', 'success')
            else:
                flash('Selected customer not found.', 'danger')
        db.session.commit()
        return redirect(url_for('admin_alerts'))

    alerts = Alert.query.order_by(Alert.created_at.desc()).all()
    return render_template('admin/alerts.html', alerts=alerts, form=form)

@app.route("/admin/alerts/mark_read/<int:alert_id>")
@login_required
@admin_required
def mark_alert_read(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    alert.is_read = True
    db.session.commit()
    flash('Alert marked as read.', 'info')
    return redirect(url_for('admin_alerts'))

# --- Admin Users / Customers ---
@app.route("/admin/users")
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route("/admin/customers")
@login_required
@admin_required
def admin_customers():
    customers = User.query.filter_by(role='customer').all()
    form = CustomerForm()
    return render_template('admin/customers.html', customers=customers, form=form)

# --- Customer Alerts ---
@app.route("/customer/alerts")
@login_required
@customer_required
def customer_alerts():
    alerts = Alert.query.filter_by(user_id=current_user.id).order_by(Alert.created_at.desc()).all()
    return render_template('customer/alerts.html', alerts=alerts)

# --- API Endpoints ---

# Dashboard stats
@app.route("/api/dashboard/stats")
@login_required
def api_dashboard_stats():
    total_devices = Device.query.count()
    online_devices_count = sum(1 for d in Device.query.all() if d.last_seen and (datetime.now(timezone.utc) - d.last_seen.replace(tzinfo=timezone.utc)).total_seconds() < 60 and not d.is_blocked)
    blocked_devices_count = Device.query.filter_by(is_blocked=True).count()
    stats = {
        'total_devices': total_devices,
        'online_devices': online_devices_count,
        'blocked_devices': blocked_devices_count,
        'alerts_count': Alert.query.filter_by(user_id=current_user.id, is_read=False).count()
    }
    return jsonify(stats)

# Devices list
@app.route("/api/devices")
@login_required
@admin_required
def api_devices():
    devices_data = []
    for d in Device.query.all():
        last_seen_aware = d.last_seen.replace(tzinfo=timezone.utc) if d.last_seen else None
        devices_data.append({
            'id': d.id,
            'name': d.device_name,
            'mac_address': d.mac_address,
            'ipv4_address': d.ip_address,
            'is_blocked': d.is_blocked,
            'last_seen': last_seen_aware.isoformat() if last_seen_aware else None,
            'user': d.user.username if d.user else 'N/A',
            'status': 'online' if last_seen_aware and (datetime.now(timezone.utc)-last_seen_aware).total_seconds()<60 else 'offline'
        })
    return jsonify(devices_data)

# Block/Unblock device
@app.route("/api/block_device/<mac_address>", methods=['POST'])
@login_required
@admin_required
def api_block_device(mac_address):
    success = router_manager.block_device(mac_address)
    if success:
        device = Device.query.filter_by(mac_address=mac_address).first()
        if device:
            device.is_blocked = True
            db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 500

@app.route("/api/unblock_device/<mac_address>", methods=['POST'])
@login_required
@admin_required
def api_unblock_device(mac_address):
    success = router_manager.unblock_device(mac_address)
    if success:
        device = Device.query.filter_by(mac_address=mac_address).first()
        if device:
            device.is_blocked = False
            db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 500

# --- Family Profiles Page ---
@app.route('/family_profiles')
@login_required
@admin_required
def family_profiles():
    try:
        profiles = router_manager.get_family_profiles()

        # Get device counts for all profiles at once
        devices_dict = router_manager.get_all_profiles_devices()

        # Normalize devices_dict keys
        devices_dict_clean = {}
        for k, v in devices_dict.items():
            key_clean = k.replace("\n", " ").replace("\r", "").replace("Enabled", "").replace("Disabled", "").strip()
            devices_dict_clean[key_clean] = v
        print(f"[DEBUG] Devices dict cleaned for UI: {devices_dict_clean}")

        for profile in profiles:
            profile_name = profile['name'].replace("\n", " ").replace("\r", "").strip()
            profile['devices'] = devices_dict_clean.get(profile_name, 0)

            # Default values
            profile.setdefault('schedules', 0)
            profile.setdefault('bedtime', 0)
            profile.setdefault('blocked_sites', 0)
            profile.setdefault('visit_attempts', 0)

        return render_template('family_profiles.html', profiles=profiles)

    except Exception as e:
        print(f"[FamilyProfiles] Error: {e}")
        return render_template('family_profiles.html', profiles=[])


# --- Profile Details Page ---
@app.route('/family_profiles/<profile_name>')
@login_required
@admin_required
def profile_details(profile_name):
    try:
        profile_name_clean = profile_name.replace("\n", " ").replace("\r", "").strip()

        # Get device count for this profile
        devices_dict = router_manager.get_all_profiles_devices()
        devices_dict_clean = {}
        for k, v in devices_dict.items():
            key_clean = k.replace("\n", " ").replace("\r", "").replace("Enabled", "").replace("Disabled", "").strip()
            devices_dict_clean[key_clean] = v

        device_count = devices_dict_clean.get(profile_name_clean, 0)

        # Get the full profile info
        profile_info = None
        profiles = router_manager.get_family_profiles()
        for profile in profiles:
            name_clean = profile['name'].replace("\n", " ").replace("\r", "").strip()
            if name_clean == profile_name_clean:
                profile_info = profile
                break

        return render_template(
            'profile_details.html',
            profile=profile_info,
            devices=device_count
        )

    except Exception as e:
        print(f"[ProfileDetails] Error loading profile '{profile_name}': {e}")
        flash('Error loading profile details', 'danger')
        return redirect(url_for('family_profiles'))


# --- Family Profiles API ---
@app.route("/api/family_profiles", methods=["GET"])
@login_required
@admin_required
def api_family_profiles():
    try:
        profiles = router_manager.get_family_profiles()
        return jsonify({"profiles": profiles})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/family_profiles/<profile_name>/enable', methods=['POST'])
@login_required
@admin_required
def enable_profile(profile_name):
    success = router_manager.enable_disable_profile(profile_name, enable=True)
    return {"status": "success" if success else "error"}


@app.route('/api/family_profiles/<profile_name>/disable', methods=['POST'])
@login_required
@admin_required
def disable_profile(profile_name):
    success = router_manager.enable_disable_profile(profile_name, enable=False)
    return {"status": "success" if success else "error"}


@app.route("/api/family_profiles/<profile_name>", methods=["DELETE"])
@login_required
@admin_required
def api_delete_family_profile(profile_name):
    try:
        success = router_manager.delete_profile(profile_name)
        return jsonify({"status": "success" if success else "failed"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Database Init ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            hashed_password = bcrypt.generate_password_hash("Afnan@123").decode('utf-8')
            db.session.add(User(
                username='admin',
                email='admin@example.com',
                role='admin',
                password_hash=hashed_password
            ))
            db.session.commit()
        router_manager.ensure_login()

    app.run(debug=True)
