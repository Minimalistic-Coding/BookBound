from flask_wtf import FlaskForm
from flask_babel import _, lazy_gettext as _l
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class CommentForm(FlaskForm):
    comment = TextAreaField(_l('Add Your Comment:'), validators=[
        DataRequired(), Length(min=1, max=1200)])
    submit = SubmitField(_l('Submit'))