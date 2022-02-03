import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or '31;lkhuvbgelkjrgblyvhkgf;ksflkjhgtrrtxfgbfg'
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'jefersonhrm1@gmail.com'  # введите свой адрес электронной почты здесь
    MAIL_PASSWORD = 'wjirjfvigtzpnagl'  # введите пароль