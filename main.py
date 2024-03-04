from flask import Flask, render_template, request ,url_for, redirect, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String
from flask_bootstrap import Bootstrap4
from forms import LoginForm


from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user




app = Flask(__name__)
app.config['SECRET_KEY'] = 'YOUR_SECRET_KEY'
bootstrap = Bootstrap4(app)

# CREATING DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///userdata.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Flask-Login  login manager setup
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)




class User(db.Model,UserMixin):
    # Using multiple inheritance to include login attributes such as is_authenticated and is_logged_in
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(1000))
    contributions : Mapped[int] = mapped_column(Integer,default=0)

with app.app_context():
    db.create_all()






# home page route
@app.route('/')
def home():
    return render_template("index.html",logged_in=current_user.is_authenticated)


# registration form route
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # hashing and salting the password
        hash_and_salted_password = generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8
        )

        # storing the hashed password in the database
        new_user = User(
            email=request.form.get('email'),
            name=request.form.get('name'),
            password=hash_and_salted_password,
            contributions = 0
        )
        user = db.session.execute(db.select(User).where( User.email == new_user.email)).scalar()
        if user :  # if user has already signed up using the email , redirect to the login page
            flash("Email already registered with a different account , Log in instead ")
            return redirect(url_for('login'))
        else :   # add the user to the database
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return render_template("index.html",logged_in=current_user.is_authenticated)

    return render_template("register.html",logged_in=current_user.is_authenticated)


@app.route('/login', methods=["POST","GET"])
def login():
    loginform = LoginForm()

    if request.method == "POST" and loginform.validate_on_submit():
        email = loginform.email.data
        password = loginform.password.data

        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if not user :
            flash("That email is not associated with any account. Please try again")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else :
            login_user(user)
            return redirect(url_for('home'))

    return render_template("login.html", form = loginform, logged_in=current_user.is_authenticated )





@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("home"))





if __name__ == "__main__":
    app.run(debug=True)
