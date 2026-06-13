from flask import render_template, flash, redirect, url_for, request
from flask import g, session, current_app
from app import db
from app.blueprints.user import bp
from app.models import User, Comment
from app.blueprints.user.forms import EditProfileForm, EmptyForm
from app.utils.pagination import paginate_elements
from flask_login import current_user, login_required
from flask_babel import _
import sqlalchemy as sa

# ------------------------------------------ PROFILE VIEW FUNCTIONS ---------------------------------------------------------

@bp.route('/<username>')
@login_required
def user_profile(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))

    form = EmptyForm()

    query = user.user_comments.select().order_by(Comment.timestamp.desc())
    comments, next_url, prev_url = paginate_elements(query=query, endpoint='user.user_profile', username=user.username)

    return render_template('profile.html', title=_('Profile'), user=user, form=form, comments=comments.items, next_url=next_url, prev_url=prev_url)


# ------------------------------------------ <------> ---------------------------------------------------------

@bp.route('/edit_profile', methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data 

        avatar_id = request.form.get("avatar_id")
        if avatar_id:
            current_user.avatar_id = avatar_id

        #Set Language Preference
        selected_lang = form.language.data
        if selected_lang in current_app.config["LANGUAGES"]:
            session['language'] = selected_lang

        db.session.commit()
        flash(_('Your changes have been saved!'))
        return redirect(url_for('user.edit_profile'))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
        form.language.data = session.get('language', 'en')

    return render_template('edit_profile.html', title=_("Edit Profile"), form=form)

# ------------------------------------------ FOLLOWING FUNCTIONS ---------------------------------------------------------

@bp.route('/follow/<username>', methods=["POST"])
@login_required
def follow(username):
    form = EmptyForm()

    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == username))

        if user is None:
            flash(_("User: %(username)s not found!", username=username))
            return redirect(url_for('main.index'))

        if user == current_user:
            flash(_("You can't follow userself!"))
            return redirect(url_for('user.user_profile', username=username))

        current_user.follow(user)
        db.session.commit()
        flash(_('You are following %(username)s!', username=username))
        return redirect(url_for('user.user_profile', username=username))
    else:
        return redirect(url_for('main.index'))

# ------------------------------------------ <------> ---------------------------------------------------------

@bp.route('/unfollow/<username>', methods=["POST"])
@login_required
def unfollow(username):
    form = EmptyForm()
    
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == username))

        if user is None:
            flash(_("User: %(username)s not found!", username=username))
            return redirect(url_for('main.index'))

        if user == current_user:
            flash(_("You can't unfollow userself!"))
            return redirect(url_for('user.user_profile', username=username))

        current_user.unfollow(user)
        db.session.commit()
        flash(_('You unfollowed %(username)s!'))
        return redirect(url_for('user.user_profile', username=username))
    else:
        return redirect(url_for('main.index'))