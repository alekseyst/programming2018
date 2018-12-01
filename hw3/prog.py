from flask import Flask
from flask import render_template, request, redirect, jsonify
from collections import Counter


NAMES = [
    'i', 'you', 'he', 'we', 'youpl', 'they', 'this', 'that', 'here', 'there',
    'lang', 'sex'
]

app = Flask(__name__)


@app.route('/')
def form():
    return render_template('form.html')


@app.route('/write')
def write():
    args_list = []

    for a in NAMES:
        args_list.append(request.args.get(a, ''))

    with open('data.csv',  'a+', encoding='utf-8') as f:
        f.write('\t'.join(args_list) + '\r')

    return redirect('/')


@app.route('/json')
def json_page():
    with open('data.csv', encoding='utf-8') as f:
        table = f.read().strip('\n')
    res = [
        {n: v for n, v in zip(NAMES, line.split('\t'))}
        for line in table.split('\n')
    ]

    return jsonify(res)


@app.route('/search')
def search():
    with open('data.csv', encoding='utf-8') as f:
        table = f.read().strip('\n')
    res = [line.split('\t') for line in table.split('\n')]

    word = request.args.get('word', '')
    sex = request.args.getlist('sex')
    sex_i = NAMES.index('sex')
    res = [
        r for r in res if r[sex_i] in sex and any(word in w for w in r[:10])]
    return render_template('search.html', results=res)


@app.route('/stats')
def stats():
    with open('data.csv', encoding='utf-8') as f:
        table = f.read().strip('\n')
    res = [line.split('\t') for line in table.split('\n')]
    words = [word for line in res for word in line[:10] if word]

    sex_i = NAMES.index('sex')
    lang_i = NAMES.index('lang')

    ctr = Counter(words)
    return render_template(
        'stats.html',
        ctr=sorted(ctr.most_common(20), key=lambda x: (-x[1], x[0])),
        total=len(words),
        male=len([r for r in res if r[sex_i] == 'male']),
        female=len([r for r in res if r[sex_i] == 'female']),
        langs=', '.join(
            sorted(list(set(r[lang_i] for r in res if r[lang_i]))))
    )


if __name__ == '__main__':
    app.run(debug=True)
