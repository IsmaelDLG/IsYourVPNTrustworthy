from flask import Flask, render_template, request, redirect, url_for
"""
https://stackabuse.com/integrating-h2-with-python-and-flask/
"""
app = Flask(__name__)

@app.route('/hello', methods=['GET'])
def index():
    return 'Hello world!'

@app.route('/hello/<name>', methods=['GET'])
def hello_name(name):
   return 'Hello %s!' % name

@app.route('/', methods = ['GET', 'POST'])
def home():
    if request.method == 'GET':
        return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    print(request.form['title'])
    print(request.form['desc'])
    print(request.form['file'])
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)