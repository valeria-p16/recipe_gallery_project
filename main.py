from flask import Flask, render_template, redirect, url_for, flash, session, request
from forms import LoginForm, RegistrationForm, RecipeForm
from base import Users, Recipes, Comments, engine, SqlAlchemyBase
from sqlalchemy.orm import sessionmaker
import os
from flask import jsonify, request
from PIL import Image
import io

Session = sessionmaker(bind=engine)
db_session = Session()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024 * 1024  # 1 ГБ


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db_session.query(Users).filter_by(login=form.username.data, password=form.password.data).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.login
            return redirect(url_for('main'))
        else:
            form.username.errors.append('Неверный логин или пароль')
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = db_session.query(Users).filter_by(login=form.username.data).first()
        if existing_user:
            form.username.errors.append('Такой логин уже существует')
        else:
            new_user = Users(login=form.username.data, password=form.password.data)
            db_session.add(new_user)
            try:
                db_session.commit()
                flash('Регистрация успешна!', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db_session.rollback()
                flash('Произошла ошибка при регистрации', 'danger')
    return render_template('register.html', form=form)


@app.route('/main')
def main():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = db_session.query(Users).filter_by(id=user_id).first()
    search_query = request.args.get('search', '').strip().lower()
    if search_query:
        search_words = search_query.split()
        all_recipes = db_session.query(Recipes).all()
        filtered_recipes = []
        for recipe in all_recipes:
            recipe_title_lower = recipe.title.lower()
            if all(
                    any(
                        word in part
                        for part in recipe_title_lower.split()
                    )
                    for word in search_words
            ):
                filtered_recipes.append(recipe)
        recipes = filtered_recipes
    else:
        recipes = db_session.query(Recipes).all()
    return render_template('main.html', user=user, recipes=recipes, search_query=search_query)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/create_recipe', methods=['GET', 'POST'])
def create_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))

        if not form.recipe_image.data:
            flash('Изображение обязательно для загрузки', 'danger')
            return render_template('create_recipe.html', form=form)

        try:
            filename = form.recipe_image.data.filename.rsplit('/', 1)[-1]  # Убираем путь
            filename = filename.encode('ascii', 'ignore').decode('ascii')
            file_ext = os.path.splitext(filename)[1].lower()
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

            if not file_ext or file_ext[1:] not in allowed_extensions:
                flash('Недопустимый формат файла', 'danger')
                return render_template('create_recipe.html', form=form)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                form.recipe_image.data.seek(0)
                with Image.open(io.BytesIO(form.recipe_image.data.read())) as img:
                    img.verify()
                    form.recipe_image.data.seek(0)
                    with open(image_path, 'wb') as f:
                        while True:
                            chunk = form.recipe_image.data.read(1024 * 1024)  # 1 МБ
                            if not chunk:
                                break
                            f.write(chunk)
            except Exception as e:
                flash(f'Ошибка при загрузке файла: {str(e)}', 'danger')
                return render_template('create_recipe.html', form=form)
            new_recipe = Recipes(
                user_id=user_id,
                title=form.recipe_name.data,
                ingredients=form.ingredients.data,
                description=form.description.data,
                image=filename
            )
            try:
                db_session.add(new_recipe)
                db_session.commit()
                flash('Рецепт успешно создан!', 'success')
                return redirect(url_for('main'))
            except Exception as e:
                db_session.rollback()
                os.remove(image_path)  # Удаляем файл при ошибке
                flash('Произошла ошибка при сохранении рецепта', 'danger')
        except Exception as e:
            flash(f'Критическая ошибка при загрузке: {str(e)}', 'danger')
            return render_template('create_recipe.html', form=form)

    return render_template('create_recipe.html', form=form)


@app.errorhandler(413)
def request_entity_too_large(error):
    flash('Файл слишком большой', 'danger')
    return redirect(url_for('create_recipe'))


@app.route('/my_recipes')
def my_recipes():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user_recipes = db_session.query(Recipes).filter_by(user_id=user_id).all()
    return render_template('my_recipes.html', user_recipes=user_recipes)


@app.route('/edit_recipe/<int:recipe_id>', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    recipe = db_session.query(Recipes).filter_by(id=recipe_id).first()
    if not recipe:
        flash('Рецепт не найден', 'danger')
        return redirect(url_for('my_recipes'))
    user_id = session.get('user_id')
    if not user_id or recipe.user_id != user_id:
        flash('У вас нет прав на редактирование этого рецепта', 'danger')
        return redirect(url_for('my_recipes'))
    form = RecipeForm(
        recipe_name=recipe.title,
        ingredients=recipe.ingredients,
        description=recipe.description
    )
    if form.validate_on_submit():
        if form.recipe_image.data:
            if recipe.image:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], recipe.image))
                except:
                    flash('Ошибка при удалении старого изображения', 'danger')
            filename = form.recipe_image.data.filename.rsplit('/', 1)[-1]
            filename = filename.encode('ascii', 'ignore').decode('ascii')
            file_ext = os.path.splitext(filename)[1].lower()
            if not file_ext or file_ext[1:] not in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
                flash('Недопустимый формат файла', 'danger')
                return render_template('edit_recipe.html', form=form, recipe=recipe)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            form.recipe_image.data.save(image_path)
            recipe.image = filename
        recipe.title = form.recipe_name.data
        recipe.ingredients = form.ingredients.data
        recipe.description = form.description.data
        try:
            db_session.commit()
            flash('Рецепт успешно отредактирован', 'success')
            return redirect(url_for('my_recipes'))
        except Exception as e:
            db_session.rollback()
            flash('Произошла ошибка при сохранении', 'danger')
    return render_template('edit_recipe.html', form=form, recipe=recipe)


@app.route('/delete_recipe/<int:recipe_id>', methods=['POST'])
def delete_recipe(recipe_id):
    recipe = db_session.query(Recipes).filter_by(id=recipe_id).first()
    if not recipe:
        flash('Рецепт не найден', 'danger')
        return redirect(url_for('my_recipes'))
    user_id = session.get('user_id')
    if not user_id or recipe.user_id != user_id:
        flash('У вас нет прав на удаление этого рецепта', 'danger')
        return redirect(url_for('my_recipes'))
    if recipe.image:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], recipe.image))
        except:
            flash('Ошибка при удалении изображения', 'danger')
    db_session.delete(recipe)
    try:
        db_session.commit()
        flash('Рецепт успешно удален', 'success')
    except:
        db_session.rollback()
        flash('Произошла ошибка при удалении', 'danger')

    return redirect(url_for('my_recipes'))


@app.route('/logout')
def logout():
    # Очищаем сессию
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Вы успешно вышли из системы', 'success')
    return redirect(url_for('index'))


@app.route('/recipe/<int:recipe_id>')
def view_recipe(recipe_id):
    recipe = db_session.query(Recipes).filter_by(id=recipe_id).first()
    if not recipe:
        flash('Рецепт не найден', 'danger')
        return redirect(url_for('main'))
    user = db_session.query(Users).filter_by(id=recipe.user_id).first()
    return render_template('view_recipe.html', recipe=recipe, author=user)


@app.route('/comments/<int:recipe_id>', methods=['GET', 'POST'])
def comments(recipe_id):
    recipe = db_session.query(Recipes).filter_by(id=recipe_id).first()
    if not recipe:
        flash('Рецепт не найден', 'danger')
        return redirect(url_for('main'))
    if request.method == 'POST':
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))
        comment_text = request.form.get('comment')
        if not comment_text:
            flash('Введите текст комментария', 'danger')
            return redirect(url_for('comments', recipe_id=recipe_id))
        new_comment = Comments(
            recipe_id=recipe_id,
            user_id=user_id,
            text=comment_text
        )
        db_session.add(new_comment)
        try:
            db_session.commit()
            flash('Комментарий добавлен', 'success')
        except Exception as e:
            db_session.rollback()
            flash('Ошибка при сохранении комментария', 'danger')
    all_comments = db_session.query(Comments).filter_by(recipe_id=recipe_id).all()
    return render_template('comments.html', recipe=recipe, comments=all_comments)


@app.route('/api/recipes', methods=['GET'])
def api_recipes():
    recipes = db_session.query(Recipes).all()
    return jsonify([
        {
            'id': recipe.id,
            'title': recipe.title,
            'ingredients': recipe.ingredients,
            'description': recipe.description,
            'image': recipe.image
        } for recipe in recipes
    ])


@app.route('/api/recipes/<int:recipe_id>', methods=['GET'])
def api_recipe(recipe_id):
    recipe = db_session.query(Recipes).filter_by(id=recipe_id).first()
    if not recipe:
        return jsonify({'error': 'Рецепт не найден'}), 404
    return jsonify({
        'id': recipe.id,
        'title': recipe.title,
        'ingredients': recipe.ingredients,
        'description': recipe.description,
        'image': recipe.image
    })


if __name__ == '__main__':
    app.run(debug=True)
