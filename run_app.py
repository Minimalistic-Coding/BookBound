import sqlalchemy as sa
import sqlalchemy.orm as so
from app import create_app, db
from app.models import User, Book, Comment, Message, Notification, Task
from app import cli

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'sa': sa, 'so': so, 'db': db, 'User': User, 'Book' : Book, 'Comment' : Comment, 'Message': Message, 'Notification': Notification, 'Task': Task}

