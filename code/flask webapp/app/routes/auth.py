from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app.forms.auth import LoginForm, RegisterForm
from app.models.user import Users
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)

@auth.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for("main.dashboard"))
        flash("Invalid credentials")
    return render_template("login.html", form=form)

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

@auth.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        # Check if the username already exists
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            flash("Username already exists. Please choose a different one.", "danger")
            # Don't redirect; render the template again with the form and error message
            return render_template("register.html", form=form, our_users=Users.query.all())
        else:
            # Hash the password
            hashed_password = generate_password_hash(form.password.data, method='sha256')

            # Create a new user with the hashed password
            new_user = Users(username=form.username.data, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("main.dashboard", user=new_user))

    # Render the form with the current data if the user submits an invalid form
    return render_template("register.html", form=form, our_users=Users.query.all())