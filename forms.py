from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FileField
from wtforms.validators import DataRequired, Length, EqualTo


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[
        DataRequired('Пожалуйста, введите логин'),
        Length(min=4, max=25, message='Длина логина должна быть от 4 до 25 символов')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired('Пожалуйста, введите пароль')
    ])
    submit = SubmitField('Войти')


class RegistrationForm(FlaskForm):
    username = StringField('Логин', validators=[
        DataRequired('Пожалуйста, введите логин'),
        Length(min=4, max=25, message='Длина логина должна быть от 4 до 25 символов')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired('Пожалуйста, введите пароль'),
        Length(min=6, message='Пароль должен содержать минимум 6 символов')
    ])
    confirm_password = PasswordField('Повторите пароль', validators=[
        DataRequired('Пожалуйста, подтвердите пароль'),
        EqualTo('password', message='Пароли не совпадают')
    ])
    submit = SubmitField('Зарегистрироваться')


class RecipeForm(FlaskForm):
    recipe_name = StringField('Название рецепта', validators=[
        DataRequired('Пожалуйста, введите название рецепта')
    ])
    ingredients = TextAreaField('Ингредиенты', validators=[
        DataRequired('Пожалуйста, укажите ингредиенты')
    ])
    description = TextAreaField('Процесс приготовления', validators=[
        DataRequired('Пожалуйста, опишите процесс приготовления')
    ])
    recipe_image = FileField('Фотография рецепта', validators=[
        DataRequired('Пожалуйста, загрузите изображение рецепта')  # Добавляем валидатор
    ])
    submit = SubmitField('Опубликовать')
