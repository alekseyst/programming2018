from flask import Flask
import os
import sqlite3
from flask import render_template, request, redirect, jsonify
from collections import Counter
from pymystem3 import Mystem

from parse_texts import parse_texts


app = Flask(__name__)

CONNECTION = None
URL = None


def create_database():
    database_url = 'db.sqlite'
    # return database_url

    try:
        os.remove(database_url)
    except FileNotFoundError:
        pass
    conn = sqlite3.connect(database_url)
    cursor = conn.cursor()

    cursor.execute("""\
CREATE TABLE pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    title TEXT,
    url TEXT,
    lang TEXT,
    value TEXT)""")

    cursor.execute("""\
CREATE TABLE words (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    word INTEGER,
    idx INTEGER,
    page_id INTEGER,
    FOREIGN KEY(page_id) REFERENCES pages(id))""")

    cursor.execute("""CREATE INDEX ix_1 ON words (word)""")

    for text in parse_texts('texts'):
        cursor.execute(
            """INSERT INTO pages(title, lang, value, url) VALUES (?,?,?,?)""",
            (text['title'], text['lang'], text['text'], text['meta']['url']))
        page_id = cursor.lastrowid
        cursor.executemany(
            """INSERT INTO words(word, idx, page_id) VALUES (?,?,?)""",
            [(word, idx, page_id) for word, idx in text['index']])
    conn.commit()

    return database_url


@app.route('/')
def form():
    query = request.args.get('query', '').strip()
    if not query:
        return render_template('index.html')
    stemmer = Mystem()
    query = (
        stemmer.analyze(query)[0].get('analysis', [])
        or [{'lex': query}])[0].get('lex', query)

    CONNECTION = sqlite3.connect(database_url)
    cursor = CONNECTION.cursor()
    cursor.execute(
        'SELECT page_id, idx FROM words WHERE word=?', (query,))
    words = cursor.fetchall()
    pages_ids = set((word[0],) for word in words)

    pages = {}
    for page_id in pages_ids:
        cursor.execute(
            'SELECT id, title, value, url FROM pages WHERE id=?', page_id)
        id_, title, value, url = cursor.fetchall()[0]
        pages[id_] = {'title': title, 'text': value, 'url': url}

    results = []
    for page_id, position in sorted(words):
        page = pages[page_id]
        results.append({
            'text': page['text'][max(0, position - 120):position + 120],
            'title': page['title'],
            'url': page['url'],
        })

    return render_template('index.html', results=results)


if __name__ == '__main__':
    database_url = create_database()
    URL = database_url
    CONNECTION = sqlite3.connect(database_url)

    app.run(debug=True)
