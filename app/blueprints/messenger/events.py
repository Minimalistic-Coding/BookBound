from flask import session, request, current_app
from flask_socketio import disconnect, join_room, leave_room, emit
from app import socketio, db
from app.models import User, Message, Notification
import sqlalchemy as sa 

@socketio.on('connect')
def handle_connection():
    token = request.args.get('token')
    if not token:
        return False 

    user = User.check_chat_connection_token(token)
    if not user:
        return False 

    session["author_id"] = user.id 

@socketio.on('disconnect')
def handle_disconnect():
    pass

@socketio.on('join_chat')
def on_join_chat(data):
    author_id = session.get('author_id')
    if not author_id:
        return False 

    partner_id = int(data.get('partner_id'))
    if not partner_id:
        return False

    room_id = f"room_{min(author_id, partner_id)}_{max(author_id, partner_id)}"
    join_room(room_id)

@socketio.on('leave_chat')
def on_leave_chat(data):
    author_id = session.get('author_id')
    partner_id = int(data.get('partner_id'))

    if author_id and partner_id:
        room_id = f"room_{min(author_id, partner_id)}_{max(author_id, partner_id)}"
        leave_room(room_id)

@socketio.on('send_message')
def handle_send_message(data):
    sender = db.session.get(User, session.get('author_id'))
    recipient = db.session.get(User, int(data.get('recipient_id')))

    if not sender or not recipient:
        return False 

    if sender.id == recipient.id:
        return False

    body = data.get('body', '').strip()
    if not body or len(body) > 2000:
        return False 

    msg = Message(author=sender, recipient=recipient, body=body)
    db.session.add(msg)
    db.session.commit()
    recipient.add_notification('unread_message_count', recipient.unread_message_count())
    db.session.commit()

    room_id = f"room_{min(sender.id, recipient.id)}_{max(sender.id, recipient.id)}"
    emit('new_message', {
            'id': msg.id,
            'sender_id': sender.id,
            'body': body,
            'timestamp': msg.timestamp.isoformat() + "Z"
        }, to=room_id)

    return {'status': 'ok'}

@socketio.on('load_history')
def handle_load_history(data):
    author_id = session.get('author_id')
    partner_id = int(data.get("partner_id"))
    oldest_msg_id = int(data.get("oldest_msg_id"))

    if not author_id or not partner_id or not oldest_msg_id:
        return False  

    query = (
        sa.select(Message)
        .where(
            sa.or_(
                sa.and_(
                    Message.sender_id == author_id,
                    Message.recipient_id == partner_id
                ),
                sa.and_(
                    Message.sender_id == partner_id,
                    Message.recipient_id == author_id
                )
            )
        )
        .where(Message.id < oldest_msg_id)
        .order_by(Message.timestamp.desc())
        .limit(current_app.config["MESSAGES_PER_CHAT"])
    )

    # BUG FIX: Forced conversion into a mutable list to let Python safely reverse order
    older_messages = list(db.session.scalars(query).all())
    older_messages.reverse()

    history_data = []
    for msg in older_messages:
        history_data.append({
                'id': msg.id,
                'sender_id': msg.sender_id,
                'body': msg.body,
                'timestamp': msg.timestamp.isoformat() + "Z"
            })

    emit('history_loaded', {
            'messages': history_data
        }, to=request.sid)
