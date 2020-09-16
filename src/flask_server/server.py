"""Server for JS Injection example

Contains a minimal implementation of a web server, using Flask.
"""
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from pathlib import Path
from werkzeug.utils import secure_filename
import db

UPLOAD_FOLDER = Path(__file__).parent.absolute().resolve() / Path('uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/hello', methods=['GET'])
def hello_world():
    """A hello world function

    :return: "Hello world!"
    :rtype: str
    """
    return 'Hello world!'

@app.route('/hello/<name>', methods=['GET'])
def hello_name(name):
    """A simple hello function, using a param

    :param name: The name of the person/thing to greet
    :type name: str

    :return: 'Hello <name>'
    :rtype: str
    """
    return 'Hello %s!' % name

@app.route('/', methods = ['GET', 'POST'])
def index():
    if request.method == 'GET':
        conn, c = db.connect()
        posts = db.get_all(c)
        conn.close()
        return render_template('index.html', posts=posts)


def _allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _upload_file(myfile):
    # if user does not select file, browser also
    # submit an empty part without filename
    if myfile and _allowed_file(myfile.filename):
        filename = secure_filename(myfile.filename)
        myfile.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return str(os.path.join(app.config['UPLOAD_FOLDER'], filename))

@app.route('/upload', methods=['POST'])
def new_post():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return redirect(url_for('index'))
            
        
        filepath = _upload_file(request.files['file'])
        conn, cursor = db.connect()

        print((request.form['title'], request.form['desc'], filepath, filepath.split('/')[-1:]))
        db.new_post(cursor, (request.form['title'], request.form['desc'], filepath, filepath.split('/')[-1:]))

        db.close(conn)
    return redirect(url_for('index'))


if __name__ == '__main__':    
    db.initialize()
    app.run('0.0.0.0', debug=True)
    db.delete()

    print('\nBye...')
