import hashlib
from datetime import datetime, timedelta
from sqlite3 import connect
from flask_session import Session
from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename


def hash(password):
    salt = hashlib.sha256(b"hashlib").digest()
    hashed_password = hashlib.sha256(f"{salt}{password}".encode()).digest()
    return salt.hex() + hashlib.sha256(hashed_password).hexdigest()


def check_auth():
    if 'logged_in' in session:
        return True
    else:
        return False


app = Flask(__name__)
allowed_extensions = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = '/loaded'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////C:/Users/Max/PycharmProjects/Projecy/acc.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'lKjO7!6xH2NG3zY4'
db = SQLAlchemy(app)
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_REFRESH_EACH_REQUEST'] = False
app.config['SESSION_COOKIE_NAME'] = 'session'
app.config['SESSION_COOKIE_DOMAIN'] = None
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(weeks=1)
app.secret_key = 'lKjO7!6xH2NG3zY4'
Session(app)

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in allowed_extensions


@app.route('/create-article')
def public_old():
    return redirect('/article/create-article')



@app.route("/article/create-article", methods=["POST", "GET"])
def create_article():
    if request.method == "POST":
        title = request.form['title']
        intro = request.form['intro']
        text = request.form['txt']
        base = connect('acc.db')
        cursor = base.cursor()
        cursor.execute('INSERT INTO articles (author,title, introtext, txt, datepublishing) VALUES (?, ?, ?, ?, ?)',
                       ("11", title, intro, text, datetime.utcnow()))
        if len(text) < 50:
            return render_template('too_low_len.html', len='50')
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


@app.route('/file/test', methods=["POST", "GET"])
def file_test():
    if request.method == 'POST':  # 1488
        file = request.files['file']
        print(file.filename)
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
    if results==[]:
        return render_template('404_article.html')
    title = results[0][0]
    intro = results[0][1]
    txt = results[0][2]
    author = results[0][3]
    date = results[0][4]
    connection.close()
    return render_template('article.html', title=title, intro=intro, text=txt, author=author, date=date)


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == 'POST':

        login = request.form['login']
        password=hash(request.form['password'])
        if login.count(' ')+login.count(' ')==len(login) or password.count(' ')+password.count(' ')==len(password):
            return render_template('login.html')
        print(login,password)
        connection = connect('acc.db')
        cursor = connection.cursor()
        cursor.execute("SELECT password,id FROM Users WHERE username=?", (login,))
        results = cursor.fetchall()
        if results==[]:
            cursor.execute("SELECT password,id FROM Users WHERE mail=?", (login,))
            results = cursor.fetchall()
        if results==[]:
            flash('Такого пользователя не существует, вам необходимо зарегистрироваться')
            return render_template('login.html')
        print(results[0][0])
        if password==results[0][0]:
            session['logged_in'] = True
            session['user_id'] = results[0][1]
            return redirect('/profile')

        flash("Неверный пароль")
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

    ide=session['user_id']
    return redirect('/profile/'+str(ide))

@app.route('/profile/<id>')
def profile(id):
    connection = connect('acc.db')
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Users WHERE id=?", (id,))
    results = cursor.fetchall()
    username=results[0][1]
    about=results[0][3]
    publicname=results[0][5]
    print(results)
    return render_template('profile.html',publicname=publicname,about=about,username=username)


if __name__ == "__main__":
    app.run(debug=True)
