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


DATABASE = 'server.db'


db = SqliteExtDatabase(DATABASE)


class MainPage(RequestHandler):
    def get(self):
        self.render('index.html', title='Тест')


class User(Model):
    id = PrimaryKeyField()
    username = CharField(unique=True)

    class Meta:
        database = db


class EchoWebSocket(WebSocketHandler):
    user_list= list()
    connections = set()

    def open(self):
        self.connections.add(self)

    def on_close(self):
        self.connections.remove(self)

    def on_message(self, message):
        import json
        json_obj = json.loads(message)

        self.write_message(json.dumps({'response':'FUCK!'}))
        if 'nickname' in json_obj:
            user = User.create(username=json_obj['nickname'])

            self.user_list.append(json_obj['nickname'])

            dump = json.dumps(dict(
                user_id=user.id,
                users=self.user_list,
            ))

            self.write_message(dump)


def main():
    import os

    db.connect()

    if not os.path.exists('server.db'):
        db.create_tables([User])

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
