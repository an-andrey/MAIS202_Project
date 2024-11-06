from flask import Flask, render_template, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user

load_dotenv()

app = Flask(__name__)

# Secret Key Configuration
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY", "FLASK_SECRET_KEY")

# Database URI and SSL Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URL")
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "connect_args": {
        'ssl': {
            'ca': 'ca.pem'  # Replace 'ca.pem' with the actual path to your CA cert file
        }
    }
}

# Initialize SQLAlchemy
db = SQLAlchemy(app)

#Flask_login 
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

#Creating a db model
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(200), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)

    #this is if we return an instance of the class
    def __repr__(self):
        return "<Name %r>" %self.username

# Create a Form Class
class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Log-in")
    

@app.route("/")
def home():
    return "Hello World"

@app.route("/db")
def get_db():
    with db.engine.connect() as connection:
        try:
            # Execute query and fetch results
            result = connection.execute(text("SELECT * FROM movies LIMIT 10;"))
            rows = result.fetchall()  # Fetch all rows from the result
            print(rows)

        except Exception as e:
            print(f"An error occurred: {e}")
    return "db!"

#login page
@app.route("/login",methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()

        #If the user exists
        if user: 
            if user.password == form.password.data:
                login_user(user)
                return redirect(url_for("dashboard"))
            else: 
                flash("incorrect password, please try again")
        else: 
            flash("user does not exist")


    return render_template("login.html", form=form)

@app.route("/logout",methods=["GET","POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

#dashboard page
@app.route("/dashboard",methods=["GET","POST"])
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/register", methods=['GET', 'POST'])
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
            # Create a new user
            new_user = Users(username=form.username.data, password=form.password.data)
            db.session.add(new_user)
            db.session.commit()
            flash("User Added Successfully", "success") 
            # Optionally redirect to the home page or another page
            return render_template("register.html", username=form.username.data, form=form, our_users=Users.query.all())  # Redirect after successful registration

    # Render the form with the current data if the user submits an invalid form
    return render_template("register.html", form=form, our_users=Users.query.all())
@app.route("/hello/<name>")
def hello(name):
    return render_template("hello_there.html", name=name)

@app.route("/predict/<int:userId>/<int:topAmount>")
def predict(userId, topAmount):
    return f"Predicting the top {topAmount} movies for {userId}"

if __name__ == "__main__":
    app.run(debug=True)