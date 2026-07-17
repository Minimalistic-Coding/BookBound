from flask_wtf import FlaskForm
from flask_babel import _, lazy_gettext as _l
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
import sqlalchemy as sa
from app import db
from app.models import User

# ------------------------------------------ <------> ---------------------------------------------------------

class LoginForm(FlaskForm):

    username = StringField(_l('Username'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign in'))

# ------------------------------------------ <------> ---------------------------------------------------------

class RegistrationForm(FlaskForm):

    username = StringField(_l('Username'), validators=[DataRequired()])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(_l('Repeat Password'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Register'))

    def validate_username(self, username):
        query = sa.select(User).where(User.username == username.data)
        user = db.session.scalar(query)

        if user is not None:
            raise ValidationError(_('Please use different Username!'))

    def validate_email(self, email):
        query = sa.select(User).where(User.email == email.data)
        user = db.session.scalar(query)

        if user is not None:
            raise ValidationError(_('Please use different Email!'))

# ------------------------------------------ <------> ---------------------------------------------------------

class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Request Password Reset'))

# ------------------------------------------ <------> ---------------------------------------------------------

class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Password Reset'))