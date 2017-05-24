"""
Рабочий http и websocket python сервер
Сервак взятый для примера: https://github.com/alxpy/simple-tornado-chat/blob/0.2/chat.py
made by: Дмитрий Юшко
"""

from tornado.web import RequestHandler, Application
from tornado.websocket import WebSocketHandler
from tornado.ioloop import IOLoop
from tornado.options import options
from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase
from tornado.escape import json_decode, json_encode
from tornado.gen import coroutine
from uuid import uuid4
import logging


logging.basicConfig(format='%(levelname)s [%(asctime)s %(filename)s line %(lineno)d] %(message)s')


DATABASE = 'server.db'


db = SqliteExtDatabase(DATABASE)


class MainPage(RequestHandler):
    def get(self):
        self.render('index.html')


class User(Model):
    id = PrimaryKeyField()
    username = CharField(unique=True)
    hash = CharField()

    class Meta:
        database = db


class Session:
    def __init__(self, **kwargs):
        self.users = kwargs
        self.map = list(range(9))
        self.step = 0

    def set_cell(self, cell, symbol):
        self.map[int(cell)] = symbol
        self.step += 1

    def check_win(self):
        win_coord = ((0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6))
        for each in win_coord:
            if self.map[each[0]] == self.map[each[1]] == self.map[each[2]]:
                return self.map[each[0]], each
        return False


class EchoWebSocket(WebSocketHandler):
    user_list= dict()
    connections = set()
    sessions = dict()

    @coroutine
    def open(self):
        self.connections.add(self)

    @coroutine
    def on_close(self):
        self.connections.remove(self)

    @coroutine
    def on_message(self, message):
        json_obj = json_decode(message)
        cmd = json_obj['cmd']

        if cmd in globals():
            func = globals()[cmd]
            logging.warning('Call function %s', func.__name__)
            yield func(self, json_obj)

@coroutine
def login(cls, json_obj):
    if 'nickname' in json_obj:
        nickname = json_obj['nickname']
        if not nickname in cls.user_list.keys():
            logging.warning('Login: %s', json_obj)
            cls.user_list[nickname] = hash(cls), cls
            cls.write_message(json_encode({'status': 'success'}))
        else:
            cls.write_message(json_encode({'status': 'fail'}))

@coroutine
def disconnect(cls, json_obj):
    nickname = json_obj['nickname']
    if nickname in cls.user_list.keys():
        logging.warning('Disconnect: %s', nickname)
        cls.connections.remove(cls.user_list[nickname][1])
        del cls.user_list[nickname]

@coroutine
def getUserList(cls, json_obj):
    nickname = json_obj['nickname']
    logging.warning('Get user list: %s Json: %s', nickname, json_obj)
    cls.write_message(json_encode({
        'users': list(i for i in cls.user_list.keys() if i != nickname)
    }))

@coroutine
def invite(cls, json_obj):
    logging.warning('Invite: %s', json_obj)

    # generate unique session id
    game_id = str(uuid4())
    json_obj['gameid'] = game_id

    # create empty session
    cls.sessions[game_id] = None

    # send invite to enemy
    enemy = cls.user_list[json_obj['enemy']][1]
    enemy.write_message(json_obj)

@coroutine
def invite_accept(cls, json_obj):
    from random import choice
    game_id = json_obj['gameid']

    logging.warning('Invite accept: %s', json_obj)

    sender = cls.user_list[json_obj['from']][1]
    enemy = cls.user_list[json_obj['enemy']][1]

    c = choice('XO')
    logging.warning('Choice: %s', c)

    sender_key = c
    enemy_key = 'O' if c == 'X' else 'X'

    logging.warning('Sender key: %s, enemy key: %s', sender_key, enemy_key)

    _dict = {sender_key:sender, enemy_key:enemy}
    cls.sessions[game_id] = Session(**_dict)

    sender.write_message(json_encode({
        'game': 'start',
        'gameid': game_id,
        'enemynickname': json_obj['enemy'],
        'key': sender_key
    }))

    enemy.write_message(json_encode({
        'game': 'start',
        'gameid': game_id,
        'enemynickname': json_obj['from'],
        'key': enemy_key
    }))

@coroutine
def invite_cancel(cls, json_obj):
    game_id = json_obj['gameid']

    if game_id in cls.sessions.keys():
        logging.warning('Invite cancel: %s', json_obj)
        del cls.sessions[game_id]

@coroutine
def game(cls, json_obj):
    # get key, cell and game id
    key, cell, game_id = json_obj['key'], json_obj['cell'], json_obj['gameid']

    logging.warning('Game: %s', json_obj)

    # get game session and set cell with key
    session = cls.sessions[game_id]
    session.set_cell(cell=cell, symbol=key)

    send_to = 'O' if key == 'X' else key
    session.users[send_to].write_message(json_encode({'gamestep': cell}))

    # if step > 4
    if session.step > 4:
        # check win
        res = session.check_win()
        if isinstance(res, tuple):
            winner, path = res
            """send win to winner and send lose to loser"""


def main():
    import os

    db.connect()

    if not User.table_exists():
        User.create_table()

    options.parse_command_line()

    settings = dict(
        warning=True,
        template_path=os.path.join(os.path.dirname(__file__), 'templates'),
        static_path=os.path.join(os.path.dirname(__file__), 'static'),
    )

    app = Application([
        (r'/', MainPage),
        (r'/ws', EchoWebSocket),
    ], **settings)

    app.listen(8000)

    try:
        IOLoop.instance().start()
    finally:
        IOLoop.instance().stop()
        db.close()


if __name__ == '__main__':
    main()
