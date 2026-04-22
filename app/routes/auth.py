"""Authentication: login, registration, logout."""
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from app import db
from app.forms import LoginForm, SignupForm
from config import Config


def register_routes(app):
    @app.route('/auth/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        form = SignupForm()
        if form.validate_on_submit():
            from app.models import User

            user = User(
                username=form.username.data.strip(),
                email=form.email.data.strip().lower(),
                role=form.role.data,
                status='active',
            )
            user.set_password(form.password.data)
            db.session.add(user)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash('Username or email is already registered.', 'danger')
                return render_template('auth/register.html', form=form)
            flash('Account created. You can sign in.', 'success')
            return redirect(url_for('login'))
        return render_template('auth/register.html', form=form)

    @app.route('/auth/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        form = LoginForm()
        if form.validate_on_submit():
            from app.models import User

            user = User.query.filter(
                (User.username == form.username.data) | (User.email == form.username.data),
                User.status == 'active',
            ).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                nxt = request.args.get('next') or url_for('dashboard')
                return redirect(nxt)
            flash('Invalid credentials or inactive account.', 'danger')
        return render_template('auth/login.html', form=form)

    @app.route('/auth/logout')
    def logout():
        logout_user()
        flash('Signed out.', 'info')
        return redirect(url_for('index'))
