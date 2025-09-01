from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from models import User  # Make sure User model is imported

# ------------------------------
# Login Form
# ------------------------------
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


# ------------------------------
# Registration Form
# ------------------------------
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('customer', 'Customer'), ('admin', 'Admin')], validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Please use a different email address.')


# ------------------------------
# Customer Form (Admin Add Customer)
# ------------------------------
class CustomerForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Add Customer')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Please use a different email address.')


# ------------------------------
# Alert Form (Admin Send Alert)
# ------------------------------
class AlertForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    message = TextAreaField('Message', validators=[DataRequired()])
    alert_type = SelectField(
        'Alert Type',
        choices=[('info', 'Info'), ('warning', 'Warning'), ('danger', 'Danger'), ('success', 'Success')],
        validators=[DataRequired()]
    )
    send_to = SelectField(
        'Send To',
        choices=[('all', 'All Customers'), ('specific', 'Specific Customer')],
        validators=[DataRequired()]
    )
    customer_id = SelectField('Customer', coerce=int)  # For specific customer
    submit = SubmitField('Send Alert')


# ------------------------------
# Delete Form (CSRF Only)
# ------------------------------
class DeleteForm(FlaskForm):
    submit = SubmitField('Delete')
