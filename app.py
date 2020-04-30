from flask import Flask, render_template, redirect, url_for, request, session, g, jsonify
from flask_nav import Nav
from flask_nav.elements import Navbar, View, Subgroup, Separator, Link
from flask_bootstrap import Bootstrap
from peewee import SqliteDatabase
from database import User, Cards
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import bcrypt  # for hashing
import re

app = Flask(__name__)
Bootstrap(app)
nav = Nav()

app.secret_key = 'SuperSecretKeyForAgileProject'
db = SqliteDatabase('pixr.sqlite')
# init for managing logins
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@nav.navigation()
def mynavbar():
    if current_user.is_authenticated:
        return Navbar(
            'Menu',
            View('Home', 'home'),
            View('Profile', 'profile'),
            View(f'Logout ({g.user.username})', 'logout')
        )
    else:
        return Navbar(
            'Menu',
            View('Home', 'home'),
            View('Login', 'login'),
            View('Register', 'register')
        )


@app.before_request
def get_db():
    """ Initialize connection with database"""
    db.connect()


@app.before_request
def before_request():
    """ For sessions """
    g.user = None
    if 'user_id' in session:
        user = User.get(User.id == session['user_id'])
        g.user = user


@app.teardown_request
def close_connection(exception):
    """ For closing database when not in use """
    if not db.is_closed():
        db.close()


@app.route('/home', methods=['GET'])
def home():
    return render_template('index.html')


@app.route('/', methods=['GET'])
def default():
    return render_template('index.html')


@login_manager.user_loader
def load_user(user_id):
    """ Required for managing user login """
    return User.get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """ Logs User in """
    error = ''
    if request.method == 'POST':
        session.pop('user_id', None) # reset session
        username = request.form["username"]
        passwd = request.form["password"]
        try:
            loginUser = User.get(User.username == username)
        except:
            return render_template('login.html', error='A user with that username does not exist.')
        if loginUser and bcrypt.checkpw(passwd.encode("utf-8"), loginUser.password.encode("utf-8")):
            # If hashed passwwords match, then generate session and login user
            print(loginUser.password)
            session["user_id"] = User.get(User.username == username).id
            login_user(loginUser)
            return redirect(url_for('profile'))
        else:
            error = "Invalid password."
            return render_template('login.html', error='')
    else:
        return render_template('login.html', error='')

@app.route('/profile')
@login_required
def profile():
    """ Displays User Profile """
    if not g.user:  # Checks user stored in session (not sure this is actually needed anymore with login manager)
        return redirect(url_for('login', error="unauthorized"))
    return render_template('profile.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """ Registers a new user and hashes password, also logs in after """
    error = ''
    if request.method == 'POST':
        username = request.form["new_username"]
        password = request.form["new_password"]

        reg = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$"

        # compiling regex
        pat = re.compile(reg)
        # searching regex
        mat = re.search(pat, password)
        # validating conditions
        if mat:
            password = request.form["new_password"].encode("utf-8")
            print("Password is valid.")
        else:

            return render_template('register.html', error="Password is invalid: \n"
                                                          "Must be 6-8 characters, \n"
                                                          "contain one number, one uppercase letter, and "
                                                          "one symbol")

        if User.select().where(User.username == username).exists():
            return render_template('register.html', error='A user with that username already exists.')
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())
        newuser = User.create(username=username, password=hashed)
        session["user_id"] = User.get(User.username == newuser.username).id
        login_user(newuser)
        return redirect(url_for('profile'))
    if request.method == 'GET':
        return render_template('register.html', error=error)


@app.route('/logout')
@login_required
def logout():
    """ Logs user out when called """
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    nav.init_app(app)
    app.run(debug=True)
