from flask import Blueprint, request, render_template, redirect , session, url_for, flash , abort
from Db import db


from Db.models import users, articles
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, login_required, current_user, logout_user
from sqlalchemy import or_


RGZ = Blueprint("RGZ",__name__)


@RGZ.route("/")
def start():
    return redirect("/RGZ/glav", code=302)

@RGZ.route("/RGZ/check")
def main():
    my_users = users.query.all()
    print(my_users)
    return "result in console!"

@RGZ.route("/RGZ/checkarticles")
def main1():
    my_articles = articles.query.all()
    print(my_articles)
    return "result in console!"

@RGZ.route('/RGZ/glav', methods=['GET'])
def RGZ_glav():
    username_form = session.get('username')
    all_users = users.query.all()
    all_profiles = []

    for user in all_users:
        user_profile = articles.query.filter_by(user_id=user.id).first()
        all_profiles.append((user, user_profile))

    return render_template('glav.html', username=username_form, all_profiles=all_profiles)
@RGZ.route("/RGZ/register", methods=["GET", "POST"])
def register():
    errors = ""
    error_password_form = ""
    error_username_from = ""

    if request.method == "GET":
        return render_template("register.html")

    username_from = request.form.get("username")
    password_form = request.form.get("password")

    if not (username_from and password_form):
        errors = "Пожалуйста, заполните все поля"
        return render_template('register.html', errors=errors)

    isUserExist = users.query.filter_by(username=username_from).first()

    if isUserExist:
        error_username_from = "Пользователь с таким именем уже существует"
        return render_template("register.html", error_username_from=error_username_from)

    if len(password_form) < 5:
        error_password_form = "Пароль должен быть 5 или больше символов"
        return render_template('register.html', error_password_form=error_password_form, password_form=password_form)

    hashedPswd = generate_password_hash(password_form, method='pbkdf2')
    newUser = users(username=username_from, password=hashedPswd)

    try:
        db.session.add(newUser)
        db.session.commit()
    except Exception as e:
        errors = f"Ошибка при регистрации: {str(e)}"
        return render_template('register.html', errors=errors)

    return redirect(url_for("RGZ.login"))

@RGZ.route("/RGZ/login", methods=["GET", "POST"])
def login():
    errors = []

    if request.method == "GET":
        return render_template("login.html")

    username_form = request.form.get("username")
    password_form = request.form.get("password")

    user = users.query.filter_by(username=username_form).first()

    if user and check_password_hash(user.password, password_form):
        login_user(user, remember=False)

        # Проверяем, заполнил ли пользователь анкету
        if not user.articles:
            return redirect(url_for("RGZ.fill_profile"))  # Перенаправляем на заполнение анкеты

        return redirect(url_for("RGZ.RGZ_glav"))

    if not (username_form and password_form):
        errors.append("Пожалуйста, заполните все поля")
    elif not user:
        errors.append("Пользователь не существует")
    else:
        errors.append("Неправильный пароль")

    return render_template("login.html", username_form=username_form, errors=errors)

@RGZ.route("/RGZ/fill_profile", methods=["GET", "POST"])
def fill_profile():
    if request.method == "GET":
        return render_template("fill_profile.html")

    # Получаем данные из формы заполнения профиля
    username = request.form.get("username")
    service_type = request.form.get("service_type")
    experience = request.form.get("experience")
    hourly_rate = request.form.get("hourly_rate")
    is_visible = request.form.get("is_visible") == "on"
    # Проверяем, чтобы все поля были заполнены
    if not (service_type and experience and hourly_rate):
        return render_template("fill_profile.html", error="Пожалуйста, заполните все поля")

    # Получаем текущего пользователя
    user = users.query.filter_by(id=current_user.id).first()

    # Создаем новую анкету и связываем с пользователем
    new_article = articles(user_id=user.id, service_type=service_type, experience=experience, hourly_rate=hourly_rate, username=username, is_visible=is_visible )
    db.session.add(new_article)
    db.session.commit()

    return redirect(url_for("RGZ.RGZ_glav"))


@RGZ.route("/RGZ/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    # Получаем текущего пользователя
    user = current_user

    if request.method == "GET":
        # Отображаем форму с текущими данными анкеты
        return render_template("edit_profile.html", user=user)

    # Получаем данные из формы редактирования профиля
    username = request.form.get("username")
    service_type = request.form.get("service_type")
    experience = request.form.get("experience")
    hourly_rate = request.form.get("hourly_rate")
    is_visible = request.form.get("is_visible") == "on"

    # Проверяем, чтобы все поля были заполнены
    if None in {service_type, experience, hourly_rate}:
        return render_template("edit_profile.html", user=user, error="Пожалуйста, заполните все поля")

    # Обновляем данные анкеты
    user.username = username

    user_profile = articles.query.filter_by(user_id=user.id).first()
    if user_profile:
        user_profile.username = username
        user_profile.service_type = service_type
        user_profile.experience = experience
        user_profile.hourly_rate = hourly_rate
        user_profile.is_visible = is_visible  # Если "on", то True, иначе False
    else:
        # Если анкеты нет, создаем новую
        new_article = articles(
            user_id=user.id, 
            service_type=service_type,
            experience=experience,
            hourly_rate=hourly_rate,
            is_visible=is_visible == "on",
            username=username
        )
        db.session.add(new_article)

    # Сохраняем изменения в базе данных
    db.session.commit()

    return redirect(url_for("RGZ.RGZ_glav"))

@RGZ.route("/RGZ/hide_profile")
@login_required
def hide_profile():
    user = users.query.filter_by(id=current_user.id).first()

    # Обновляем флаг видимости анкеты
    if user.articles:
        user.articles.is_visible = False

        db.session.commit()

    return redirect(url_for("RGZ.glav"))

@RGZ.route("/RGZ/delete_account", methods=["GET", "POST"])
@login_required
def delete_account():
    if request.method == "GET":
        return render_template("delete_account.html")

    # Если пользователь подтвердил удаление аккаунта
    if request.form.get("confirm_delete"):
        user_id = current_user.id
        user = users.query.get(user_id)

        # Проверяем, существует ли пользователь
        if user:
            # Удаляем анкету пользователя, если она существует
            if user.articles:
                # Удаляем все анкеты пользователя
                for article in user.articles:
                    db.session.delete(article)

            # Удаляем пользователя
            db.session.delete(user)

            # Сохраняем изменения в базе данных
            db.session.commit()

            # Выход из системы
            logout_user()

            return redirect(url_for("RGZ.RGZ_glav"))

    # Если пользователь не подтвердил удаление, вернуть на страницу подтверждения
    return render_template("delete_account.html")
    
@RGZ.route('/RGZ/search_profiles', methods=['GET', 'POST'])
def search_profiles():
    page = int(request.args.get('page', 1))
    per_page = 5

    if request.method == 'POST':
        # Получаем параметры поиска из формы
        username = request.form.get('username')
        service_type = request.form.get('service_type')
        experience_min = request.form.get('experience_min')
        experience_max = request.form.get('experience_max')
        hourly_rate_min = request.form.get('hourly_rate_min')
        hourly_rate_max = request.form.get('hourly_rate_max')

        # Выполняем поиск в базе данных
        query = articles.query.join(users).filter(
            users.username.ilike(f"%{username}%") if username else True,
            articles.service_type.ilike(f"%{service_type}%") if service_type else True,
            articles.experience.between(experience_min, experience_max) if experience_min and experience_max else True,
            articles.hourly_rate.between(hourly_rate_min, hourly_rate_max) if hourly_rate_min and hourly_rate_max else True,
            articles.is_visible.is_(True)
        )

        pagination = query.paginate(page=page, per_page=per_page)
        search_results = pagination.items

        return render_template('search_results.html', search_results=search_results, page=page, has_next=pagination.has_next, has_prev=pagination.has_prev)

    return render_template('search_profiles.html')

@RGZ.route("/RGZ/admin", methods=["GET", "POST"])
@login_required  # Декоратор, требующий аутентификации
def admin():
    admin_user = users.query.get(1)
    if admin_user:
    # Назначаем статус администратора
        admin_user.is_admin = True

    # Проверка, является ли текущий пользователь администратором
    if not admin_user:
        abort(403)  # Возвращает ошибку 403 Forbidden, если пользователь не является администратором

    if request.method == "GET":
        # Получите список всех пользователей из базы данных
        all_users = users.query.all()
        return render_template("admin.html", all_users=all_users)

    if request.method == "POST":
        # Обработка запроса на удаление аккаунта
        user_id_to_delete = request.form.get("user_id")
        user_to_delete = users.query.get(user_id_to_delete)
        user_id_to_edit = request.form.get("user_id")
        
        if user_to_delete:
            # Удаляем анкету пользователя, если она существует
            if user_to_delete.articles:
                for article in user_to_delete.articles:
                    db.session.delete(article)

            # Удаляем пользователя
            db.session.delete(user_to_delete)
            db.session.commit()

            return redirect(url_for("RGZ.admin"))

        flash("Пользователь не найден", "error")
        return redirect(url_for("RGZ.glav"))

@RGZ.route("/RGZ/admin/edit_profile/<int:user_id>", methods=["GET", "POST"])
@login_required
def admin_edit_profile(user_id):
    # Получаем пользователя по ID
    user = users.query.get(user_id)

    if not user:
        flash("Пользователь не найден", "error")
        return redirect(url_for("RGZ.admin"))

    user_profile = articles.query.filter_by(user_id=user.id).first()

    if request.method == "POST":
        # Получаем данные из формы редактирования профиля
        service_type = request.form.get("service_type")
        experience = request.form.get("experience")
        hourly_rate = request.form.get("hourly_rate")
        is_visible = request.form.get("is_visible")

        # Проверяем, чтобы все поля были заполнены
        if None in {service_type, experience, hourly_rate}:
            flash("Пожалуйста, заполните все поля", "error")
            return redirect(url_for("RGZ.admin_edit_profile", user_id=user.id))

        # Обновляем данные анкеты
        if user_profile:
            user_profile.service_type = service_type
            user_profile.experience = experience
            user_profile.hourly_rate = hourly_rate
            user_profile.is_visible = is_visible == "on"
        else:
            # Если анкеты нет, создаем новую
            new_article = articles(
                user_id=user.id,
                service_type=service_type,
                experience=experience,
                hourly_rate=hourly_rate,
                is_visible=is_visible == "on"
            )
            db.session.add(new_article)

        # Сохраняем изменения в базе данных
        db.session.commit()
        flash("Профиль пользователя успешно обновлен", "success")
        return redirect(url_for("RGZ.admin_edit_profile", user_id=user.id))

    return render_template("admin_edit_profile.html", user=user, user_profile=user_profile)

@RGZ.route('/RGZ/logout')
@login_required
def logout():
    logout_user()
    return redirect('/RGZ/glav')