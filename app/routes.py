import datetime
import os
from werkzeug.utils import secure_filename
from app.emai import send_password_reset_email
from app.forms import ResetPasswordForm
from app import app
from flask import request, send_from_directory
from flask import render_template, flash, redirect, url_for
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, ResetPasswordRequestForm, BeExpertForm
from app.Models import Users
from flask_login import logout_user, login_required, login_user, current_user
from werkzeug.urls import url_parse
from app import bd
db = bd.Data()


@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Users().get(form.username.data)
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('auth'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('auth.html', title='Sign In', form=form)


@app.route('/index')
@login_required
def index():
    # GET
    db.cursor.execute('Select title from category')
    posts = db.cursor.fetchall()
    if current_user.is_anonymous:
        return redirect(url_for('auth'))
    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for('index')
    else:
        return redirect(f"/index/{next_page}")
    return render_template('home.html', title='Home', posts=posts)


@app.route('/index/<category_name>', methods=['GET', 'POST'])
@login_required
def index_next(category_name):
    # Выборка видосов по категории
    db.cursor.execute('SELECT id from category where title = %s', (category_name,))
    category = db.cursor.fetchall()[0]
    db.cursor.execute('Select id, title from models where category_id = %s', (category, ))
    posts = db.cursor.fetchall()
    if current_user.is_anonymous:
        return redirect(url_for('auth'))
    return render_template('after_index.html', title='Home', posts=posts, category_name=category_name)


@app.route('/index/<category_name>/<models_category>', methods=['GET', 'POST'])
@login_required
def index_next_models(category_name, models_category):
    # Выборка моделей по категории
    # db.cursor.execute('SELECT * from video where models = %s', (models_category,))
    db.cursor.execute('''SELECT v.id, v.video_path, v.description, v.title, v.rating, v.author_id, v.views_users, u.username 
           FROM video v INNER JOIN users u ON u.id=v.author_id where models = %s''', (str(models_category),))
    posts = db.cursor.fetchall()
    print(posts)
    if request.args.get('search'):
        req = request.args.get('search')
        db.cursor.execute("Select * from video where title = %s and models = %s", (req, models_category, ))
        posts = db.cursor.fetchall()
    if current_user.is_anonymous:
        return redirect(url_for('auth'))
    return render_template('where_models.html', title='Home', posts=posts, category_name=category_name,
                           models_category=models_category)


@app.route('/index/<category_name>/<models_category>/<id_post>', methods=['GET', 'POST'])
@login_required
def index_next_next(category_name, models_category, id_post):
    # Выбрать всё из этого видоса
    db.cursor.execute('''SELECT v.id, v.video_path, v.description, v.title, v.rating, v.author_id, u.username 
        FROM video v INNER JOIN users u ON u.id=v.author_id WHERE v.id = %s;''', (str(id_post), ))

    posts = db.cursor.fetchall()
    if posts[0][6] != current_user.username:
        db.cursor.execute('Select views_users from video where id = %s', (str(id_post), ))
        views = db.cursor.fetchall()[0][0]
        if views:
            views = views + 1
            db.cursor.execute('Update video set views_users = %s where id = %s', (str(views), str(id_post)))
        else:
            db.cursor.execute('Update video set views_users = %s where id = %s', (str(1), str(id_post)))
    db.cursor.execute('''SELECT c.id id, c.video_id, c.content, c.reply_to, c.user_id, u.username 
                        FROM comment c INNER JOIN users u ON u.id=c.user_id WHERE c.reply_to is null and c.video_id = %s;''',
                      (str(id_post), ))
    comms = db.cursor.fetchall()
    comms_id = [i[0] for i in iter(comms)]
    reply_comms = []
    for i in iter(comms_id):
        db.cursor.execute('''SELECT c.id id, c.video_id, c.content, c.reply_to, c.user_id, u.username
                          FROM comment c INNER JOIN users u ON u.id=c.user_id WHERE reply_to = %s and video_id = %s''',
                          (str(i), str(id_post)))
        reply_comms.append(db.cursor.fetchall())
    comments = list()
    for i in comms:
        for j in reply_comms:
            if len(j) > 0:
                if i[0] == j[0][3]:
                    i = list(i)
                    i.append(j)
        comments.append(i)
    if current_user.is_anonymous:
        return redirect(url_for('auth'))
    if request.method == 'POST':  # Тут ответ на комментарий
        if request.form.get('comment'):  # Обычный комментарий
            db.cursor.execute('insert into comment (video_id, user_id, content, reply_to) values (%s, %s, %s, null)',
                              (str(id_post), str(current_user.id), str(request.form.get('comment')),))
        if request.form.get('help'):
            db.cursor.execute('insert into helpers (message, user_id, expert_id, when_sent) values (%s, %s, %s, %s)',
                              (str(request.form.get('help')), str(current_user.id), str(posts[0][5]),
                               datetime.datetime.utcnow(),))
        if request.form.getlist('rating'):  # Рейтинг
            db.cursor.execute('Select * from rating where user_id=%s and content_id= %s', (str(current_user.id), str(id_post)),)
            if db.cursor.fetchall():
                db.cursor.execute('UPDATE rating set rate = %s where user_id=%s and content_id= %s',
                                  (request.form.getlist('rating')[0], str(current_user.id), str(id_post)))
            else:
                db.cursor.execute('INSERT into rating (user_id, content_id, rate) values (%s, %s, %s)',
                                  (str(current_user.id), str(id_post), request.form.getlist('rating')[0]))
            db.conn.commit()
        for i in comms_id:  # Ответ на комментарий
            if request.form.get(str(i)):
                db.cursor.execute('insert into comment (video_id, user_id, content, reply_to) values (%s, %s, %s, %s)',
                                  (str(id_post), str(current_user.id), str(request.form.get(str(i))), str(i),))

    return render_template('after_after_index.html', title='Home', posts=posts[0], comms=comments)


# Позволяет видосы открывать из статика/видеос
@app.route('/cdn/<path:filename>')
def custom_static(filename):
    return send_from_directory(app.config['CUSTOM_STATIC_PATH'], filename)


@app.route("/logout")
@login_required
def logout():
    db.cursor.execute("UPDATE users	SET last_seen = '%s' where username = '%s';"
                      % (datetime.datetime.utcnow(), current_user.username))
    logout_user()
    return redirect(url_for('auth'))


@app.route('/change_passwd', methods=['GET', 'POST'])
def change_passwd():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = Users().get_by_email(email=form.email.data)
        if user:
            send_password_reset_email(user)
            pass
        flash('Check your email for the instructions to reset your password')
        # return redirect(url_for('login'))
    return render_template('change_password.html',
                           title='Reset Password', form=form)


@app.route('/change_passwd/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = Users().verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password)
        flash('Your password has been reset.')
        return redirect(url_for('auth'))
    return render_template('res_passwd.html', form=form)


@app.route('/reg', methods=['GET', 'POST'])
def reg():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if form.validate_username(form.username) and form.validate_email(form.email):
            users = Users().add(form.username, form.email, form.password)
            user = Users().get(users.data)
            login_user(user)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)
    return render_template('regisrt.html', title='Sign Up', form=form)


@app.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    form = PostForm()
    user = Users().get(username)
    user.about(user.id)
    db.cursor.execute('Select title from roles where id = %s', (str(user.role), ))
    role = db.cursor.fetchone()
    db.cursor.execute('SELECT title from category')
    categories = db.cursor.fetchall()
    if categories:
        categories = [x[0] for x in categories]
        form.category.choices = categories
    time = user.last_seen
    db.cursor.execute('SELECT title from models')
    models = db.cursor.fetchall()
    if models:
        models = [x[0] for x in models]
        form.models.choices = models  # Все модели вывести
    db.cursor.execute('SELECT * from video where author_id = %s', (str(user.id), ))
    video = db.cursor.fetchall()
    db.cursor.execute('SELECT h.id, h.message, h.user_id, h.when_sent, u.username from helpers h inner join users u '
                      'on h.user_id = u.id where expert_id = %s', (str(user.id), ))
    helps = db.cursor.fetchall()
    zapros = None
    if current_user.role == 1:
        db.cursor.execute('SELECT h.id, h.user_id, h.email, h.phone, h.about, h.date_sent,'
                          ' u.username from wanaexp h inner join users u '
                          'on h.user_id = u.id')
        zapros = db.cursor.fetchall()
    if request.method == 'POST':
        if current_user.role == 1:
            if request.form.get('category'):
                db.cursor.execute("Insert into category (title) VALUES (%s)", (str(request.form.get('category')), ))
            if request.form.get('models'):
                db.cursor.execute("Insert into models (title, category_id) VALUES (%s, %s)",
                                  (str(request.form.get('category')), ))
            db.cursor.execute('select id from wanaexp where user_id = %s', (str(request.form.get('users_exp')), ))
            id = db.cursor.fetchall()[0]
            db.cursor.execute('UPDATE users_roles set role_id = 2 where user_id=%s',
                              (str(request.form.get('users_exp')),))
            db.cursor.execute('Delete from wanaexp where id = %s', (str(id[0]),))
        else:
            db.cursor.execute('Select id from video')
            id_filename = db.cursor.fetchall()[-1][0] + 1
            db.cursor.execute('Select id from models where title = %s', (form.models.data,))
            model_id = db.cursor.fetchone()[0]
            file = request.files['file']
            filename = secure_filename(file.filename)  # Он тогда не будет сохранять с русскими символами
            filename = filename.split('.')
            if len(filename) >= 2:
                filename = str(user.username) + str(id_filename) + '.' + filename[1]
            else:
                filename = str(user.username) + str(id_filename) + '.' + filename[0]
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            path = filename
            db.cursor.execute('Insert into video (video_path, description, title, author_id, models) values '
                              '(%s, %s, %s, %s, %s)', (path, form.post.data, form.title.data, user.id, model_id))

    return render_template('user.html', user=user, form=form, role=role, time=time, video=video, about=user.about_me,
                           helps=helps, zapros=zapros)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if request.method == 'POST':
        db.cursor.execute('Select about_me from users where username = %s', (str(current_user.username),))
        about = db.cursor.fetchall()[0]
        if request.form.get('about_p'):
            db.cursor.execute("UPDATE users	SET about_me = %s where username = %s;", (str(request.form.get('about_p')),
                                                                                      str(current_user.username)))
        if current_user.username != form.username.data:
            db.cursor.execute("UPDATE users	SET username = %s where username = %s;", (str(form.username.data),
                                                                                      str(current_user.username)))

        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username

    return render_template('edit_profile.html', title='Edit Profile', form=form)


@app.route('/be_expert', methods=['GET', 'POST'])
@login_required
def be_expert():
    form = BeExpertForm()
    if request.method == 'POST':
        db.cursor.execute('Insert into wanaexp (user_id, email, phone, about, date_sent) values (%s, %s, %s, %s, %s)',
                          (str(current_user.id), str(form.email.data), str(form.phone.data),
                           str(form.text.data), datetime.datetime.utcnow(), ))
        flash('Succesful')
        return redirect(url_for('index'))
    return render_template('be_exp.html', title='Be expert', form=form)


@app.errorhandler(500)
def err(error):
    # db.session.rollback()
    return render_template('error.html', title='Error'), 500


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404
