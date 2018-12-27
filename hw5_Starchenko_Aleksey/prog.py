from flask import Flask
from flask import render_template, request, redirect, jsonify
from collections import Counter


app = Flask(__name__)


@app.route('/')
def form():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
