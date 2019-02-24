import re
import os
import sqlite3
from pymystem3 import Mystem


def parse_text(path, stemmer):
    with open(path, encoding='utf-8') as f:
        text = f.read()
    meta = dict([
        a[1:].split(' ', 1)
        for a in text.split('\n') if a.startswith('@')])
    text_paragr = [a for a in text.split('\n') if not a.startswith('@')]
    text = '\n'.join(filter(None, text_paragr))

    lem_text = stemmer.analyze(text)

    i = 0
    words = []
    text = []
    position = 0
    for lem in lem_text:
        word = lem['text']
        key = lem.get('analysis')
        if key is not None:
            if not key:
                key = word.lower()
            else:
                key = key[0]['lex']
            words.append((key, position))
        text.append(word)

        position += len(word) + 1

    return {
        'text': ''.join(text),
        'meta': meta,
        'index': words
    }


def get_texts(prefix):
    texts = []
    path = os.path.join(prefix, 'metadata.csv')
    with open(path, encoding='utf-8') as metadata_file:
        for line in metadata_file:
            line = line.strip().split('\t')
            path, title, *other, lang = [a for a in line if a]
            yield {
                'path': os.path.join(prefix, path),
                'title': title,
                'other': other,
                'lang': lang,
            }


def parse_texts(prefix):
    stemmer = Mystem()
    for text in get_texts(prefix):
        text.update(parse_text(text['path'], stemmer))
        text['meta'].update({'other': text.pop('other')})
        yield text
