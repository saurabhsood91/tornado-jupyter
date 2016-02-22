import tornado.ioloop
import tornado.web
import jupyter_client

class MainHandler(tornado.web.RequestHandler):
    def post(self):
        code = self.get_argument("code")
        self.write("Hello, world")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
