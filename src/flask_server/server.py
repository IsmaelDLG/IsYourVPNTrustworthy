"""Server for JS Injection example

Contains a minimal implementation of a web server, using Flask.
"""
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from pathlib import Path
from werkzeug.utils import secure_filename
import string
import random
import sqlite3
from flask import g

DATABASE = str(Path(__file__).parent.absolute().resolve() / Path("db.sqlite3"))


UPLOAD_FOLDER = Path(__file__).parent.absolute().resolve() / Path("static")
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/hello", methods=["GET"])
def hello_world():
    """A hello world function

    :return: "Hello world!"
    :rtype: str
    """
    return "Hello world!"


@app.route("/hello/<name>", methods=["GET"])
def hello_name(name):
    """A simple hello function, using a param

    :param name: The name of the person/thing to greet
    :type name: str

    :return: 'Hello <name>'
    :rtype: str
    """
    return "Hello %s!" % name


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html", posts=query_db("SELECT * FROM posts"))


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _upload_file(myfile):
    # if user does not select file, browser also
    # submit an empty part without filename
    if myfile and _allowed_file(myfile.filename):
        gen_name = secure_filename(myfile.filename)
        filename = (
            gen_name
            if gen_name != ""
            else "".join(random.choice(string.ascii_letters) for _ in range(10))
        )
        myfile.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        return os.path.join(app.config["UPLOAD_FOLDER"], filename).__str__()


@app.route("/upload", methods=["POST"])
def new_post():
    if request.method == "POST":
        # check if the post request has the file part
        if "file" not in request.files:
            return redirect(url_for("index"))

        filepath = _upload_file(request.files["file"])

        print((request.form["title"], request.form["desc"], filepath, str(filepath.split('/')[-1])))

        query_db(
            "INSERT INTO posts  VALUES (?, ?, ?, ?);",
            (request.form["title"], request.form["desc"], filepath, str(filepath.split('/')[-1],))
        )
        
    return redirect(url_for('index'))

# Database stuff

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    
        """def _make_dicts(cursor, row):
            return dict((cursor.description[idx][0], value) for idx, value in enumerate(row))
        """
        db.row_factory = sqlite3.Row

    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

if __name__ == "__main__":
    app.run("0.0.0.0", debug=True)
    print("\nBye...")
