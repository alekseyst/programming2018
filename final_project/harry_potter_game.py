#!/usr/bin/env python3
# coding: utf-8

import collections
import json
import random
import re
import time

import markovify
import telebot
from telebot.types import (
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
)
import flask

import conf


WEBHOOK_HOST = 'hpgame552.herokuapp.com'
WEBHOOK_PORT = 443  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_URL_BASE = "https://{}:{}".format(WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{}/".format(conf.TOKEN)
WEBHOOK_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP addr
WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Path to the ssl private key

HELP_MESSAGE_TEXT = """\
Добро пожаловать! \
Вам предлагается сыграть в игру, в которой нужно будет отличить человека \
от компьютера. Игра состоит из пяти раундов. В каждом раунде Вы получаете \
два предложения -- нужно указать то, которое действительно было в \
одной из книг Дж. Роулинг серии "Гарри Поттер". \
Для запуска игры введите /play. Чтобы остановить игру введите \
/stop. Чтобы снова увидеть это сообщение введите /help"""

QUESTION_HELP_TEXT = """\
Попробуйте угадать, какое предложение было создано человеком, \
а какое сгенерировала машина. Укажите номер предложения, взятого \
из реального текста:\n"""

STOP_MESSAGE_TEXT = """Вы остановили игру. Для начала игры введите /play"""
INVALID_ANSWER_TEXT = """Выберите вариант ответа из допустимых"""
RESULTS_MESSAGE_TEXT = """\
Ваш счет: {score}.\n\
Правильные ответы:\n{answers}\n\n\
Введите /play, чтобы сыграть ещё."""


telebot.apihelper.proxy = {
    'https': 'socks5h://geek:socks@t.geekclass.ru:7777'
}


def load_model(sentences):
    return markovify.NewlineText('\n'.join(sentences))


def load_sentences(corpus_sents_path='etc/corpus_sents.json', min_size=40):
    with open(corpus_sents_path) as corpus_sents:
        sentences = json.load(corpus_sents)
        sentences = [sent for sent in sentences if len(sent) > min_size]
        return sentences

SENTENCES = load_sentences()
MODEL = load_model(SENTENCES)
GAMES = collections.defaultdict()

Variant = collections.namedtuple('Variant', 'text is_correct')


def get_variantes(model, sentences, max_chars=110):
    variantes = {
        random.choice([sent for sent in sentences if len(sent) < max_chars]): True
    }
    sent = model.make_short_sentence(max_chars=max_chars)
    while len(variantes) < 2:
        variantes.setdefault(sent, False)

    variantes = [
        Variant(text=text, is_correct=is_correct)
        for text, is_correct in variantes.items()
    ]

    random.shuffle(variantes)
    return variantes


class Game:
    ROUNDS_NUMBER = 5
    def __init__(self):
        self.score = 0
        self.round = 0
        self.history = []
        self.answers = []

    def get_variantes(self):
        variantes = get_variantes(MODEL, SENTENCES)
        self.history.append(variantes)
        self.round += 1
        return variantes

    def answer(self, variant_number):
        if variant_number is None:
            return False
        if 0 <= variant_number < len(self.history[-1]):
            if self.history[-1][variant_number].is_correct:
                self.score += 1
            return True
        return False

    @property
    def active(self):
        return self.round < self.ROUNDS_NUMBER

    def get_score(self):
        return '{}/{}'.format(self.score, len(self.history))

    def get_correct_answers(self):
        correct = []
        for variants in self.history:
            for variant in variants:
                if variant.is_correct:
                    correct.append(variant.text)
                    break
        return '\n\n'.join(correct)


def render_round_buttons(data):
    markup = ReplyKeyboardMarkup(True, True)
    markup.add(*(
        InlineKeyboardButton('Вариант {}'.format(i))
        for i in range(1, len(data)+1)))
    return markup


def render_question(data):
    question = '''{help}\n{variantes}'''
    variantes = []
    for i, variant in enumerate(data, 1):
        variantes.append('Вариант {i}: {variant}'.format(
            i=i, variant=variant.text))
    return question.format(
        help=QUESTION_HELP_TEXT,
        variantes='\n'.join(variantes))


def get_answer(text):
    res = re.match(r'(Вариант ?)?(?P<answer>\d+)', text)
    if not res:
        return None
    return int(res.group("answer")) - 1


def init_game(message):
    try:
        chat_id = message.chat.id
        game = Game()
        GAMES[chat_id] = game

        variantes = game.get_variantes()
        message = bot.send_message(
            message.chat.id,
            render_question(variantes),
            reply_markup=render_round_buttons(variantes))
        bot.register_next_step_handler(message, play_round)
    except Exception:
        bot.reply_to(message, 'oooops')
        raise


def play_round(message):
    try:
        game = GAMES.get(message.chat.id)
        if not game:
            return

        is_valid = game.answer(get_answer(message.text))
        if not is_valid:
            if message.text == '/stop':
                message = bot.send_message(
                    message.chat.id,
                    STOP_MESSAGE_TEXT, reply_markup=ReplyKeyboardRemove())
            else:
                message = bot.send_message(
                    message.chat.id,
                    INVALID_ANSWER_TEXT,
                    reply_markup=render_round_buttons(game.history[-1]))
                bot.register_next_step_handler(message, play_round)
            return

        if not game.active:
            finish_game(game, message)
            return

        variantes = game.get_variantes()
        message = bot.send_message(
            message.chat.id,
            render_question(variantes),
            reply_markup=render_round_buttons(variantes))

        bot.register_next_step_handler(message, play_round)
    except Exception:
        bot.reply_to(message, 'oooops')
        raise


def finish_game(game, message):
    try:
        message = bot.send_message(
            message.chat.id,
            RESULTS_MESSAGE_TEXT.format(
                answers=game.get_correct_answers(),
                score=game.get_score()))
    except Exception:
        bot.reply_to(message, 'oooops')
        raise


bot = telebot.TeleBot(conf.TOKEN)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(message.chat.id, HELP_MESSAGE_TEXT)


@bot.message_handler(commands=['play'])
def play(message):
    init_game(message)


bot.remove_webhook()
time.sleep(0.1)
bot.set_webhook(
    url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH)
    # certificate=open(WEBHOOK_SSL_CERT, 'r'))

bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()


app = flask.Flask(__name__)

   
@app.route('/', methods=['GET', 'HEAD'])
def index():
    return 'ok'

@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    flask.abort(403)
    return ''


if __name__ == '__main__':
    app.run(
        host=WEBHOOK_LISTEN,
        port=WEBHOOK_PORT,
        # ssl_context=(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV),
        debug=True)
