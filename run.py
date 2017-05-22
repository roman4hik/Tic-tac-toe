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


class EchoWebSocket(WebSocketHandler):
    user_list= dict()
    connections = set()

    @coroutine
    def open(self):
        self.connections.add(self)

    @coroutine
    def on_close(self):
        self.connections.remove(self)

    def send_user_list(self):
        for con in self.connections:
            con.write_message(json_encode({
                'status': 'success',
                'users': {k: v[0] for k, v in self.user_list.items()}
            }))

    @coroutine
    def on_message(self, message):
        json_obj = json_decode(message)
        cmd = json_obj['cmd']

        if cmd in globals():
            func = globals()[cmd]
            func(self, json_obj)


def login(cls, json_obj):
    if 'nickname' in json_obj:
        nickname = json_obj['nickname']
        if not nickname in cls.user_list.keys():
            cls.user_list[nickname] = hash(cls), cls
            cls.send_user_list()
        else:
            cls.write_message(json_encode({'status': 'Login fail!'}))


def disconnect(cls, json_obj):
    nickname = json_obj['nickname']
    if nickname in cls.user_list.keys():
        cls.connections.remove(cls.user_list[nickname][1])
        del cls.user_list[nickname]
        cls.send_user_list()
    else:
        cls.write_message(json_encode({'status': 'Disconnect fail!'}))


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
