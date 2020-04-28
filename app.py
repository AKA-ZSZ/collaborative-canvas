from flask import Flask, render_template, redirect, url_for, request, session, g, jsonify
from peewee import SqliteDatabase
from database import User, Cards
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import bcrypt  # for hashing

app = Flask(__name__)
app.secret_key = 'SuperSecretKeyForAgileProject'
db = SqliteDatabase('clicker.sqlite')
# init for managing logins
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


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


@app.route('/')
def home():
    return render_template('index.html')


@login_manager.user_loader
def load_user(user_id):
    """ Required for managing user login """
    return User.get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """ Logs User in """
    error = None
    if request.method == 'POST':
        session.pop('user_id', None) # reset session
        username = request.form["username"]
        passwd = request.form["password"]
        loginUser = User.get(User.username == username)
        if loginUser and bcrypt.checkpw(passwd.encode("utf-8"), loginUser.password.encode("utf-8")):
            # If hashed passwwords match, then generate session and login user
            print(loginUser.password)
            session["user_id"] = User.get(User.username == username).id
            login_user(loginUser)
            return redirect(url_for('profile'))
        else:
            error = "Invalid Login Credentials"
            return render_template('login.html', error=error)
    else:
        return render_template('login.html', error=error)

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
    if request.method == 'POST':
        username = request.form["new_username"]
        password = request.form["new_password"].encode("utf-8")
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())
        newuser = User.create(username=username, password=hashed)
        session["user_id"] = User.get(User.username == newuser.username).id
        login_user(newuser)
        return redirect(url_for('profile'))


@app.route('/logout')
@login_required
def logout():
    """ Logs user out when called """
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
