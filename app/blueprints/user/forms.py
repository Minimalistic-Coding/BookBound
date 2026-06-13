from flask_wtf import FlaskForm
from flask_babel import _, lazy_gettext as _l
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
import sqlalchemy as sa
from app import db
from app.models import User

# ------------------------------------------ <------> ---------------------------------------------------------

class EditProfileForm(FlaskForm):

    username = StringField(_l('Username'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About Me'), validators=[Length(min=0, max=140)])
    language = SelectField(_l('Language'), choices=[
            ('en', 'English'),
            ('es', 'Español'),
            ('ru', 'Русский'),
            ('ur', 'اردو'),
            ('ar', 'العربية')
        ])
    submit = SubmitField(_l('Submit'))

    def __init__(self, orignal_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orignal_username = orignal_username

    def validate_username(self, username):
        if username.data != self.orignal_username:
            query = sa.select(User).where(User.username == username.data)
            user = db.session.scalar(query)

            if user is not None:
                raise ValidationError(_('Please use different Username!'))
    
# ------------------------------------------ <------> ---------------------------------------------------------

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit') 