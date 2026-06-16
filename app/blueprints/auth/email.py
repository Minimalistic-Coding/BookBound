from app.utils.email_helper import send_email
from flask import render_template, current_app
from flask_babel import _

def send_password_reset_email(user):
	token = user.get_reset_password_token()
	send_email(
				_('[BookBound] - Reset Password'),
				recipients=[user.email],
				sender=current_app.config['ADMINS'][1],
				text_body=render_template('email_messages/reset_password.txt', user=user, token=token),
				html_body=render_template('email_messages/reset_password.html', user=user, token=token))