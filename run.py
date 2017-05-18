from tornado.web import RequestHandler, Application
from tornado.websocket import WebSocketHandler
from tornado.ioloop import IOLoop
from tornado.options import options


"""
Рабочий http и websocket python сервер
Сервак взятый для примера: https://github.com/alxpy/simple-tornado-chat/blob/0.2/chat.py
made by: Дмитрий Юшко
"""


class BaseHandler(RequestHandler):
	"""docstring for BaseHandler"""
	def get(self):
		self.write('Hello, World!')


class TestHandler(BaseHandler):
	"""docstring for TestHandler"""
	def get(self):
		self.write('Тут пока пусто...')


class ChatHandler(BaseHandler):
	"""docstring for Chat"""
	def get(self):
		context = dict(title='Main')
		self.render('index.html', **context)


class EchoWebSocket(WebSocketHandler):
	"""docstring for EchoWebSocket"""
	connections = set()

	def open(self):
		self.connections.add(self)

	def on_close(self):
		self.connections.remove(self)

	def on_message(self, message):
		print('New message:', message)
		for conn in self.connections:
			conn.write_message('You message: %s\n' % message)


def main():
	import os
	
	options.parse_command_line()
	
	settings = dict(
		debug=True,
		template_path=os.path.join(os.path.dirname(__file__), 'templates'),
		static_path=os.path.join(os.path.dirname(__file__), 'static'),
	)
	
	app = Application([
		(r'/', BaseHandler),
		(r'/log', TestHandler),
		(r'/chat', ChatHandler),
		(r'/ws', EchoWebSocket),
	], **settings)
	
	app.listen(8000)
	
	try:
		IOLoop.instance().start()
	except:
		IOLoop.instance().stop()


if __name__ == '__main__':
	main()
