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
from tornado.gen import coroutine, sleep
from uuid import uuid4


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
    def __init__(self, user_1, user_2):
        self.user_1, self.user_2 = user_1, user_2
        self.map = list(range(9))
        self.steep = 0

    def foo(self, cell, symbol):
        if self.steep > 4:
            return self.check_win()
        self.steep += 1
        self.map[cell] = symbol

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
    invites = dict()

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
            yield func(self, json_obj)

@coroutine
def login(cls, json_obj):
    if 'nickname' in json_obj:
        nickname = json_obj['nickname']
        if not nickname in cls.user_list.keys():
            cls.user_list[nickname] = hash(cls), cls
            cls.write_message(json_encode({'status': 'success'}))
        else:
            cls.write_message(json_encode({'status': 'fail'}))

@coroutine
def disconnect(cls, json_obj):
    nickname = json_obj['nickname']
    if nickname in cls.user_list.keys():
        cls.connections.remove(cls.user_list[nickname][1])
        del cls.user_list[nickname]

@coroutine
def getUserList(cls, json_obj):
    nickname = json_obj['nickname']
    cls.write_message(json_encode({
        'users': list(i for i in cls.user_list.keys() if i != nickname)
    }))
    for con in cls.connections:
        if con != cls:
            con.write_message(json_encode({
                'users': list(cls.user_list.keys())
            }))

@coroutine
def invite(cls, json_obj):
    cls.invites['id'] = json_obj['id'] = str(uuid4())
    from_user = json_obj['addEnemy']
    invited_user_con = cls.user_list[from_user][1]
    invited_user_con.write_message(json_obj)

@coroutine
def invite_accept(cls, json_obj):
    invite_id = json_obj['id']

@coroutine
def invite_cancel(cls, json_obj):
    pass

@coroutine
def session(cls, json_obj):
    session_id = uuid4()
    cls.sessions[session_id] = Session(None, None)


def main():
    import os

    db.connect()

    if not User.table_exists():
        User.create_table()

    options.parse_command_line()

    settings = dict(
        debug=True,
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
