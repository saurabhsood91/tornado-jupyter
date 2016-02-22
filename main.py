import tornado.ioloop
import tornado.web
import jupyter_client
import json
from queue import Empty

class MainHandler(tornado.web.RequestHandler):
    def post(self):
        code = self.get_argument("code")

        kernel_manager = jupyter_client.KernelManager()
        kernel_manager.name = "python3"
        kernel_manager.start_kernel()
        kernel = kernel_manager.client()
        msg_id = kernel.execute(code)
        print(msg_id)

        while True:
            print('stuck here')
            try:
                msg = kernel.shell_channel.get_msg()
                print(msg)
            except Empty:
                print('Empty')
                # This indicates that something bad happened, as AFAIK this should return...
                # self.log.error("Timeout waiting for execute reply")
                # raise KnitpyException("Timeout waiting for execute reply.")
            if msg['parent_header'].get('msg_id') == msg_id:
                # It's finished, and we got our reply, so next look at the results
                break
            else:
                print('something')
                # not our reply
                # self.log.debug("Discarding message from a different client: %s" % msg)
                continue


        # Now look at the results of our code execution and earlier completion requests
        # We handle messages until the kernel indicates it's ide again
        status_idle_again = False
        while True:
            print('stuck here now')
            try:
                msg = kernel.get_iopub_msg()
            except Exception:
                print('Empty')
                # There should be at least some messages: we just executed code!
                # The only valid time could be when the timeout happened too early (aka long
                # running code in the document) -> we handle that below
                # self.log.warn("Timeout waiting for expected IOPub output")
                break

            print(msg['parent_header'].get('msg_id') != msg_id)
            if msg['parent_header'].get('msg_id') != msg_id:
                if msg['parent_header'].get(u'msg_type') != u'is_complete_request':
                    print('output')
                    # not an output from our execution and not one of the complete_requests
                    # self.log.debug("Discarding output from a different client: %s" % msg)
                else:
                    print('something too')
                    # complete_requests are ok
                continue

            # Here we have some message which corresponds to our code execution
            msg_type = msg['msg_type']
            content = msg['content']

            print('Out')

            # The kernel indicates some status: executing -> idle
            if msg_type == 'status':
                if content['execution_state'] == 'idle':
                    # When idle, the kernel has executed all input
                    status_idle_again = True
                    break
                else:
                    # the "starting execution" messages
                    continue
            elif msg_type == 'clear_output':
                # we don't handle that!?
                # self.log.debug("Discarding unexpected 'clear_output' message: %s" % msg)
                continue
            ## So, from here on we have a messages with real content
            self.write(msg)

        if not status_idle_again:
            pass
            # self.log.error("Code lines didn't execute in time. Don't use long-running code in "
                        #    "documents or increase the timeout!")
            # self.log.error("line(s): %s" % lines)
        self.write(json.dumps([]))

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
