from flask import render_template, flash, redirect, url_for, request
from flask import g, current_app
from app import db
from app.blueprints.messenger import bp
from app.blueprints.main.forms import SearchForm
from app.models import User, Message
from flask_babel import _, get_locale
from flask_login import login_required, current_user
import sqlalchemy as sa
from datetime import datetime, timezone

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())

@bp.route('/inbox')
@login_required
def inbox():
    current_user.last_message_read_time = datetime.now(timezone.utc)
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()

    subq = (
        sa.select(sa.func.max(Message.id))
        .where((Message.sender_id == current_user.id) | (Message.recipient_id == current_user.id))
        .group_by(
            sa.case(
                (Message.sender_id == current_user.id, Message.recipient_id), 
                else_=Message.sender_id
            )
        )
        .subquery()
    )

    query = (
        sa.select(Message)
        .where(Message.id.in_(subq))
        .order_by(Message.timestamp.desc())
        .options(sa.orm.joinedload(Message.author), sa.orm.joinedload(Message.recipient))
    )

    latest_messages = db.session.scalars(query).all()

    inbox_data = []
    for msg in latest_messages:
        chat_partner = msg.recipient if msg.author == current_user else msg.author
        inbox_data.append({'user': chat_partner, 'msg': msg})

    return render_template('inbox.html', title="Inbox", inbox_data=inbox_data)

@bp.route('/chat/<username>')
@login_required
def chat(username):
    if current_user.username == username:
        flash(_('You cannot message yourself!'))
        return redirect(url_for('messenger.inbox'))

    user = db.first_or_404(sa.select(User).where(User.username == username))
    token = current_user.get_chat_connection_token()

    query = (
        sa.select(Message)
        .where(
            sa.or_(
                sa.and_(Message.sender_id == current_user.id, Message.recipient_id == user.id),
                sa.and_(Message.sender_id == user.id, Message.recipient_id == current_user.id)
            )
        )
        .order_by(Message.timestamp.desc())
        .limit(current_app.config["MESSAGES_PER_CHAT"])
    )

    latest_messages = list(db.session.scalars(query).all())
    latest_messages.reverse()

    return render_template('chat.html', title=_("Chat with %(username)s", username=user.username), user=user, token=token, messages=latest_messages)
