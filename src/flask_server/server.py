from flask import Flask, render_template, request, redirect, url_for

"""Server for JS Injection example

Contains a minimal implementation of a server.
"""
app = Flask(__name__)

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
        return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    """ See for more: `Origin <https://stackabuse.com/integrating-h2-with-python-and-flask/>`_
    """
    print(request.form['title'])
    print(request.form['desc'])
    print(request.form['file'])
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)
