from flask_wtf import FlaskForm
from flask_babel import _, lazy_gettext as _l
from wtforms import TextAreaField, SubmitField, StringField, SelectField
from wtforms.validators import DataRequired, Length
from flask import request

class CommentForm(FlaskForm):
    comment = TextAreaField(_l('Add Your Comment:'), validators=[
        DataRequired(), Length(min=1, max=1200)])
    submit = SubmitField(_l('Submit'))

class SearchForm(FlaskForm):
    q = StringField(_l("Search"), validators=[DataRequired()])
    search_type = SelectField(_l('Filter'), choices=[
            ('books', _l('Books')),
            ('users', _l('Users')),
        ], default='books')

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'meta' not in kwargs:
            kwargs['meta'] = {'csrf': False}
        super(SearchForm, self).__init__(*args, **kwargs)