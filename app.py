from flask import Flask, render_template, request, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_session import Session
from sqlite3 import connect
import os


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


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in allowed_extensions


@app.route('/create-article')
def public_old():
    return redirect('/article/create-article')


@app.route("/article/create-article", methods=["POST", "GET"])
def create_article():
    flash('lopapopa')
    if request.method == "POST":
        title = request.form['title']
        intro = request.form['intro']
        text = request.form['txt']
        print(len(title) == title.count(' '), len(intro) == intro.count(' '), len(text) == text.count(' '),
              len(text) < 50)
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

        return render_template('create_article.html')


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
    if request.method == 'POST':
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
        username = request.form['username']
        password = request.form['password']

        connection = connect('acc.db')
        cursor = connection.cursor()
        cursor.execute("SELECT password FROM Users WHERE username = ?", (username,))
        results = cursor.fetchall()
        connection.close()
        return str(results)
    else:
        return render_template('login.html')


if __name__ == "__main__":
    app.run(debug=True)
