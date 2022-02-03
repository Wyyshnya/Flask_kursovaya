from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, FileField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from app.bd import Data
from app.Models import Users
db = Data()


class LoginForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign in')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])  # , Email()
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user_id = db.filter_auth(username=username.data)
        if user_id is not None:
            raise ValidationError('Please use a different username.')
        else:
            return True

    def validate_email(self, username):
        user_id = db.filter_email(username=username.data)
        if user_id is not None:
            raise ValidationError('Please use a different email address.')
        else:
            return True


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])


class PostForm(FlaskForm):
    category = SelectField('Выберите категорию', coerce=str)
    models = SelectField('Выберите модель', coerce=str)
    title = StringField('Про что вы расскажете?', validators=[DataRequired(), Length(min=1, max=1000)])
    post = TextAreaField('Добавьте описание или инструкцию к видео', validators=[DataRequired(), Length(min=1, max=1000)])
    file = FileField('Загрузите видео', validators=[FileRequired('File was empty!')])
    submit = SubmitField('Отправить')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')


class BeExpertForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired()])
    text = TextAreaField('Расскажите про свой опыт', validators=[DataRequired(), Length(min=1, max=1000)])
