from time import time
from app import login
from flask_login import UserMixin
from app.bd import Data
from werkzeug.security import check_password_hash, generate_password_hash
from hashlib import md5
import jwt
from app import app


@login.user_loader
def load_user(user_id):
    return Users().get_w(user_id)


class Users(UserMixin):
    def __init__(self):
        self.db = Data()
        self.id = None
        self.username = None
        self.password = None
        self.email = None
        self.last_seen = None
        self.about_me = None
        self.role = None

    def add(self, username, email, password):
        passwd = generate_password_hash(password.data)
        self.db.cursor.execute("INSERT INTO users (username, password, email) values (%s, %s, %s)",
                               (username.data, passwd, email.data))
        self.db.conn.commit()
        self.db.cursor.execute("Select id from users where username =%s", (str(username.data),))
        id = self.db.cursor.fetchone()[0]
        self.db.cursor.execute("Insert into users_roles (user_id, role_id) values (%s, 3)", (str(id),))
        return username

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravavatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def get(self, username):
        self.db.cursor.execute("SELECT * FROM users where username = %s", (username,))
        user = self.db.cursor.fetchone()
        self.id = user[0]
        self.username = user[1]
        self.password = user[2]
        self.email = user[3]
        self.last_seen = user[4]
        self.db.cursor.execute("SELECT role_id FROM users_roles where user_id = %s", (self.id,))
        user = self.db.cursor.fetchone()
        self.role = user[0]
        return self

    def get_w(self, username):
        self.db.cursor.execute("SELECT * FROM users where id = %s", (username,))
        user = self.db.cursor.fetchone()
        self.id = user[0]
        self.username = user[1]
        self.password = user[2]
        self.email = user[3]
        self.db.cursor.execute("SELECT role_id FROM users_roles where user_id = %s", (self.id,))
        user = self.db.cursor.fetchone()
        self.role = user[0]
        return self

    def about(self, id):
        self.db.cursor.execute("SELECT about_me FROM users where id = %s", (str(id),))
        self.about_me = self.db.cursor.fetchone()[0]
        return self

    def get_by_email(self, email):
        self.db.cursor.execute("SELECT * FROM users where email = %s", (email,))
        user = self.db.cursor.fetchone()
        self.id = user[0]
        self.username = user[1]
        self.password = user[2]
        self.email = user[3]
        self.last_seen = user[4]
        self.db.cursor.execute("SELECT role_id FROM users_roles where user_id = %s", (self.id,))
        user = self.db.cursor.fetchone()
        self.role = user[0]
        return self

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, passwd):
        passwd = generate_password_hash(passwd.data)
        self.db.cursor.execute("update users set password = %s where username = %s",
                               (passwd, self.username, ))
        self.db.conn.commit()
        return self

    def check_password(self, passwd):
        # self.db.cursor.execute('SELECT password from users '
        #                     'where id = %s', (int(self.id),))
        return check_password_hash(self.password, passwd)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').encode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except Exception:
            return
        return Users().get_w(id)
