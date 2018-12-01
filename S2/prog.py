from flask import Flask
from flask import url_for, render_template, request, redirect

app = Flask(__name__)

a = '<br><a href="/">Ссылка на главную страницу<a><br><a href="/form">Ссылка на форму<a>'

@app.route('/')
def index():
    with open('lang_codes.csv', encoding='utf-8') as f:
        langs = f.read().replace('\n', '<br>').replace(',', ' — ')
    return (langs + a)

@app.route('/langs/<beg>')
def show_langs(beg):
    langs = []
    with open('lang_codes.csv', encoding='utf-8') as f:
        for line in f:
            if line.split(',')[1].lower().startswith(beg.lower()):
                langs += [line.split(',')[0]]
    return ('<br>'.join(langs) + a)

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/decide')
def decide():
    with open('lang_codes.csv', encoding='utf-8') as f:
        for line in f:
            if line.split(',')[0].lower() == request.args['lang'].lower():
                return redirect('/lang/%s' % line.split(',')[1].strip())
        else:
            return redirect(url_for('not_found'))

@app.route('/not_found')
def not_found():
    return ('Язык не найден(' + a)

@app.route('/lang/<code>')
def show_lang(code):
    letter_langs = []
    with open('lang_codes.csv', encoding='utf-8') as f:
        for line in f:
            if line.split(',')[1].strip() == code:
                lang_name = line.split(',')[0]
            if line.split(',')[1][0] == code[0]:
                letter_langs += [line.split(',')[0]]
    letter_langs = ', '.join(letter_langs)
    return render_template('lang.html', lang_name=lang_name, code=code, letter_langs=letter_langs)

if __name__ == '__main__':
    app.run(debug=True)
