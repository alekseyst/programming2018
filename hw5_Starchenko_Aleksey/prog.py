from flask import Flask
from flask import render_template, request, redirect, jsonify
from collections import Counter

from parse_texts import parse_texts


app = Flask(__name__)


@app.route('/')
def form():
    return render_template('index.html')


if __name__ == '__main__':
    for text in parse_texts('texts'):
        print(text)
    app.run(debug=True)
