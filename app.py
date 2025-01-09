import hashlib
import random
from datetime import datetime, timedelta
from sqlite3 import connect

from flask import Flask, render_template, request, redirect, session, flash
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

from flask_session import Session

app = Flask(__name__)
allowed_extensions = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = '/loaded'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////C:/Users/Max/PycharmProjects/Projecy/acc.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'lKjO7!6xH2NG3zY4'
app.config['MAX_CONTENT_PATH'] = 1024 ** 2 * 5
db = SQLAlchemy(app)
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_REFRESH_EACH_REQUEST'] = False
app.config['SESSION_COOKIE_NAME'] = 'session'
app.config['MAIL_DEBUG'] = app.debug
app.config['SESSION_COOKIE_DOMAIN'] = None
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(weeks=1)
Session(app)
app.secret_key = 'lKjO7!6xH2NG3zY4'
app.config['MAIL_SERVER'] = 'smtp.yandex.ru'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'Bloopbloop2025@yandex.ru'
app.config['MAIL_DEFAULT_SENDER'] = 'Bloopbloop2025@yandex.ru'
app.config['MAIL_PASSWORD'] = 'xhlaplrirfjjjtci'
mail = Mail(app)


def send_mail(subject, sender, recipients, html_body):
    msg = Message(
        subject=subject,
        sender=sender,
        recipients=recipients
    )
    msg.html = html_body
    mail.send(msg)




def hash(password):
    salt = hashlib.sha256(b"hashlib").digest()
    hashed_password = hashlib.sha256(f"{salt}{password}".encode()).digest()
    return salt.hex() + hashlib.sha256(hashed_password).hexdigest()


def check_auth():
    if 'logged_in' in session:
        return True
    else:
        return False


def good_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def random_code(l):
    s = ''
    for i in range(l):
        s += str(random.choice(['G', 'R', 'B', 'Y', '1', '2', '3', '4', '5', '6', '7', '8', '9']))
    return str(s)


def check_delta(t1, id):
    date1 = datetime.strptime(t1, '%Y-%m-%d %H:%M:%S.%f')
    date2 = datetime.strptime(str(datetime.utcnow()), '%Y-%m-%d %H:%M:%S.%f')
    raz = abs(date1 - date2).total_seconds()
    if raz >= 600:
        base = connect('acc.db')
        cursor = base.cursor()
        cursor.execute("DELETE FROM Users WHERE ID = ?", (id,))
        base.commit()
        return True
    return False


@app.route('/create-article')
def public_old():
    return redirect('/article/create-article')


@app.route("/article/create-article", methods=["POST", "GET"])
def create_article():
    if request.method == "POST":
        if not check_auth():
            flash('Для создания статьи необходимо зарегистрироваться')
            redirect('login')
        title = request.form['title']
        intro = request.form['intro']
        text = request.form['txt']
        base = connect('acc.db')
        cursor = base.cursor()
        cursor.execute('INSERT INTO articles (author,title, introtext, txt, datepublishing) VALUES (?, ?, ?, ?, ?)',
                       (session['user_id'], title, intro, text, datetime.utcnow()))
        if len(text) - text.count(' ') - text.count(' ') < 70:
            flash('Длина текста не может быть меньше 70 символов(не считая пробелов)')
            return render_template('create_article.html')
        elif len(title) != title.count(' ') and len(intro) != intro.count(' ') and len(text) != text.count(
                ' ') and title != ' ' and intro != ' ' and text != ' ':
            base.commit()
            base.close()
            return redirect('/article/success')
        else:
            return redirect('/article/public_error')
    else:
        if check_auth():
            return render_template('create_article.html')
        flash("Для публикации статьи необходимо войти или зарегистрироваться")
        return redirect('/login')


@app.route('/article/success')
def article_success():
    connection = connect('acc.db')
    cursor = connection.cursor()
    last_article_query = "SELECT * FROM Articles ORDER BY ID DESC LIMIT 1;"
    cursor.execute(last_article_query)
    article = cursor.fetchone()
    return render_template('article_success.html', name='/article/' + str(article[0]))


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.route('/')
def home():
    return render_template('Home.html')


@app.route('/test/code')
def test_code():
    return render_template("Mail_code.html", code='777')


@app.route('/file/test', methods=["POST", "GET"])
def file_test():
    if request.method == 'POST':  # 1488
        file = request.files['file']

        filename = secure_filename(file.filename)
        file.save('/static/photo')
    else:
        return render_template("file_test.html")


@app.route('/article/public_error')
def public_error():
    return render_template('public_error.html')


@app.route('/article/cause_problem')
def cause_problem():
    return render_template('cause_problem.html')


@app.route('/article/<id>')
def article(id):
    connection = connect('acc.db')
    cursor = connection.cursor()
    cursor.execute("SELECT Title,Introtext,txt,Author,datepublishing FROM Articles WHERE ID = ?", (id,))
    results = cursor.fetchall()
    if not results:
        return render_template('404_article.html')
    title = results[0][0]
    intro = results[0][1]
    txt = results[0][2]
    author = results[0][3]
    date = results[0][4]
    connection.close()

    if int(author) == int(session['user_id']):
        return render_template('article_adm.html', title=title, intro=intro, text=txt, author=author, date=date, id=id)
    return render_template('article.html', title=title, intro=intro, text=txt, author=author, date=date)


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = hash(request.form['password'])
        if login.count(' ') + login.count(' ') == len(login) or password.count(' ') + password.count(' ') == len(
                password):
            return render_template('login.html')

        connection = connect('acc.db')
        cursor = connection.cursor()
        cursor.execute("SELECT password,id,confirm,date_reg FROM Users WHERE username=?", (login,))
        results = cursor.fetchall()
        if not results:
            cursor.execute("SELECT password,id,confirm,date_reg FROM Users WHERE mail=?", (login,))
            results = cursor.fetchall()
        if not results:
            flash('Такого пользователя не существует, вам необходимо зарегистрироваться')
            return render_template('login.html')
        id=results[0][1]
        if results[0][2] != "True":
            if check_delta(results[0][3], id):
                flash('Время на подтверждение вышло')
                return redirect('/register')
            flash('Учетная запись не подтверждена, ссылка для подтверждения уже на вашей почте, наверное...😅😅')
            return render_template('login.html')
        if password == results[0][0]:
            session['logged_in'] = True
            session['user_id'] = results[0][1]
            return redirect('/profile')
        flash("Неверный логин или пароль")
        return redirect('/profile')
    else:
        if check_auth():
            return redirect('/profile')
        else:
            return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    return redirect('/')


@app.route('/profile')
def pre_profile():
    if check_auth():
        return redirect('/profile/' + str(session['user_id']))
    else:
        return redirect('/login')


@app.route('/profile/<id>')
def profile(id):
    connection = connect('acc.db')
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Users WHERE id=?", (id,))
    results = cursor.fetchall()
    if not results:
        if check_auth():
            return render_template('unfind_profile.html', pre='')
        else:
            return render_template('unfind_profile.html', pre='Самое время его создать')
    username = results[0][1]
    cursor.execute("SELECT * FROM Articles WHERE author=?", (id,))
    res = cursor.fetchall()

    if not res:
        res = ''

    about = results[0][3]
    publicname = results[0][5]
    if results[0][6] == "True":
        if not about:
            about = ''

        if int(session['user_id']) != int(id):
            return render_template('profile.html', public_name=publicname, about=about, username=username, articles=res)
        else:
            return render_template('profile_edit.html', public_name=publicname, about=about, username=username,
                                   articles=res)
    else:
        return render_template('unfind_profile.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        if check_auth():
            return redirect('/profile')
        login = request.form['login']
        password = request.form['password']
        password2 = request.form['password2']
        email = request.form['email']
        if login.count(' ') + login.count(' ') == len(login) or password.count(' ') + password.count(' ') == len(
                password) or email.count(' ') + email.count(' ') == len(email):
            flash('Поля не могут быть пустыми')
            return render_template('register.html', value_login=login, value_password=password, value_email=email)
        if password != password2:
            flash("Пароли не совпадают")
            return render_template('register.html', value_login=login, value_password=password, value_email=email)
        connection = connect('acc.db')
        cursor = connection.cursor()
        cursor.execute("SELECT ID FROM Users WHERE username=?", (login,))
        if cursor.fetchone():
            flash("Пользователь с таким логином уже существует")
            connection.close()
            return render_template('register.html', value_login=login, value_password=password, value_email=email)
        connection.close()
        connection = connect('acc.db')
        cursor = connection.cursor()
        cursor.execute("SELECT ID FROM Users WHERE mail=?", (email,))
        if cursor.fetchone():
            flash("Пользователь с такой электронной почтой уже существует")
            return render_template('register.html', value_login=login, value_password=password, value_email=email)
        if len(password)-password.count(' ')-password.count(' ')!=len(password):
            flash("В пароле нельзя использовать пробелы")
            return render_template('register.html', value_login=login, value_email=email)
        if len(password)<8:
            flash("Длина пароля не может быть меньше 8 символов")
            return render_template('register.html', value_login=login, value_password=password, value_email=email)
        connection = connect('acc.db')
        cursor = connection.cursor()
        cursor.execute(
            'INSERT INTO Users (username, password, mail, publicname, confirm,date_reg,sended) VALUES (?, ?, ?, ?, ?,?,?)',
            (login, hash(password), email, login, random_code(5), datetime.utcnow(), False))
        connection.commit()
        cursor.execute("SELECT ID FROM Users WHERE username=?", (login,))
        id = cursor.fetchone()[0]
        connection.close()
        return redirect('/confirm/' + str(id))
    else:
        if check_auth():
            return redirect('/profile')
        else:
            return render_template('register.html')


@app.route('/confirm/<id>', methods=['POST', 'GET'])
def confirm(id):
    if request.method == 'GET':
        connection = connect('acc.db')
        cursor = connection.cursor()
        cursor.execute("SELECT mail,confirm FROM Users WHERE id=?", (id,))
        mail_date_code = cursor.fetchone()
        cursor.execute("SELECT sended FROM Users WHERE id=?", (id,))
        try:
            if mail_date_code[1] == 'True':
                flash('Аккаунт уже подтвержден')
                return redirect('/profile')
            if cursor.fetchone()[0] == 'True':
                return render_template('confirm.html')
        except:
            return redirect('/error')
        if mail_date_code:
            mailie = str(mail_date_code[0])
            codie = str(mail_date_code[1])
            send_mail('Подтверждение регистрации', 'Bloopbloop2025@yandex.ru', [mailie],
                      render_template('Mail_code.html', code=str(mail_date_code[1])))
            cursor.execute("UPDATE Users SET sended=? WHERE id=?", ("True", id))
            connection.commit()
            connection.close()
            return render_template('confirm.html', mail=mailie)
        return redirect('/error')
    elif request.method == 'POST':
        connection = connect('acc.db')
        cursor = connection.cursor()
        cursor.execute("SELECT confirm FROM Users WHERE id=?", (id,))
        result = cursor.fetchone()
        cursor.execute("SELECT date_reg FROM Users WHERE id=?", (id,))
        resultat = cursor.fetchone()
        if check_delta(resultat[0], id):
            flash('Время на подтверждение вышло')
            return redirect('/register')
        connection.close()
        code = request.form['code']

        if not result:
            return redirect('/error')

        if code.count(' ') + code.count(' ') == len(code):
            flash('Код не может быть пустым')
            return render_template('confirm.html')
        if code == result[0]:
            connection = connect('acc.db')
            cursor = connection.cursor()
            cursor.execute("UPDATE Users SET confirm=? WHERE id=?", ("True", id))
            connection.commit()
            session['logged_in'] = True
            session['user_id'] = id
            flash('Вы успешно зарегистрированы')
            return redirect('/profile')
        elif code != result[0]:

            flash('Код неверный')
            return render_template('confirm.html')
        else:
            return redirect('/error')


@app.route('/test/mail')
def mail_test():
    send_mail('Подтверждение регистрации', 'Bloopbloop2025@yandex.ru', ['maxim.zlygostev@gmail.com'],
              render_template('Mail_code.html', code=2))
    return 'Success'


@app.route('/error')
def error_ror():
    return render_template('unexcept_error.html')


@app.route('/delete/<id>', methods=['POST', 'GET'])
def delete(id):
    if request.method == 'GET':
        connection = connect('acc.db')
        cursor = connection.cursor()
        cursor.execute("SELECT author FROM Articles WHERE id=?", (id,))
        author = cursor.fetchone()
        if not author:
            if check_auth():
                return render_template('no_rights.html', want='Если хотите, вы всегда можете ее создать')
            return render_template('no_rights.html', want='')
        if int(author[0]) != int(session['user_id']):
            return render_template('no_rights.html')
        return render_template('confidence.html', id=id)
    elif request.method == 'POST':
        connection = connect('acc.db')
        cursor = connection.cursor()
        cursor.execute("SELECT author FROM Articles WHERE id=?", (id,))
        result = cursor.fetchone()
        if not result:
            return render_template('no_rights.html')
        conf = request.form['confident']
        print(conf)
        if conf == "True":
            base = connect('acc.db')
            cursor = base.cursor()
            cursor.execute("DELETE FROM Articles WHERE ID = ?", (id,))
            base.commit()
            flash('Статья была удалена')
            return redirect('/profile')
        else:
            return redirect('/profile')


@app.route('/test/conf')
def test_conf():
    return render_template('confidence.html')


@app.route('/test/editing')
def test_editing():
    return render_template('redct.html')


@app.route('/editing/<id>', methods=['POST', 'GET'])
def editing(id):
    if request.method == 'GET':
        connection = connect('acc.db')
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Articles WHERE id=?", (id,))
        result = cursor.fetchone()
        connection.close()
        if not result:
            return redirect('/error')
        result = result
        print(result)
        title = result[2]
        intro = result[3]
        text = result[4]
        if int(result[1]) != int(session['user_id']):
            return render_template('no_rights.html')
        return render_template('redct.html', title=title, intro=intro, textarea=text, id=id)
    elif request.method == 'POST':
        connection = connect('acc.db')
        cursor = connection.cursor()
        title = request.form['title']
        intro = request.form['intro']
        text = request.form['txt']
        cursor.execute("SELECT title,Introtext,txt  FROM Articles WHERE id=?", (id,))
        result = cursor.fetchone()
        if result[0] == title and result[1] == intro and result[2] == text:
            flash('Ничего не изменилось😅')
            return render_template('redct.html', title=title, intro=intro, textarea=text, id=id)
        cursor.execute("UPDATE Articles SET Title=?,introtext=?,txt=?,datepublishing=?  WHERE id=?",
                       (title, intro, text, datetime.utcnow(), id))
        if len(text) - text.count(' ') - text.count(' ') < 70:
            flash('Длина текста не может быть меньше 70 символов(не считая пробелов)')
            return render_template('redct.html', title=title, intro=intro, textarea=text, id=id)
        elif len(title) != title.count(' ') and len(intro) != intro.count(' ') and len(text) != text.count(
                ' ') and title != ' ' and intro != ' ' and text != ' ':
            connection.commit()
            connection.close()
            return redirect('/article/success')


@app.route('/articles')
def all_articles():
    connection = connect('acc.db')
    cursor = connection.cursor()
    cursor.execute("SELECT *  FROM Articles ORDER BY id DESC")
    sessio = str(check_auth())
    return render_template('all_articles.html', articles=cursor.fetchall(), session=sessio,
                           idenf=int(session["user_id"]))


if __name__ == "__main__":
    app.run(debug=True)
# але суки юбилейная строчка🥳🥳🥳🥳🥳🥂🥂🥂🥂🥂🥂🎄🎄🎄🎄🎄🎆🎆🎆🎆🎆🎆
