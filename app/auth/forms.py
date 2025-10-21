from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class RegisterForm(FlaskForm):
    email = StringField("E-mail", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Пароль", validators=[DataRequired(), Length(min=8, max=128)])
    password2 = PasswordField("Повторите пароль", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Зарегистрироваться")

class LoginForm(FlaskForm):
    email = StringField("E-mail", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Войти")

class ForgotPasswordForm(FlaskForm):
    email = StringField("E-mail", validators=[DataRequired(), Email(), Length(max=255)])
    submit = SubmitField("Отправить ссылку для сброса")

class ResetPasswordForm(FlaskForm):
    password = PasswordField("Новый пароль", validators=[DataRequired(), Length(min=8, max=128)])
    password2 = PasswordField("Повторите пароль", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Сменить пароль")
