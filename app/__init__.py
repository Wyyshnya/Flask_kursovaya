from flask import Flask
from config import Config
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment

app = Flask(__name__, static_folder='static')
app.config.from_object(Config)
app.config['UPLOAD_FOLDER'] = './app/static/videos'
app.config['CUSTOM_STATIC_PATH'] = './static/videos'
# app.debug = True
login = LoginManager(app)
login.login_view = 'auth'
mail = Mail(app)
moment = Moment(app)

from app import routes



