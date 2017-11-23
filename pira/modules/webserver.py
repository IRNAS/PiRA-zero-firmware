from __future__ import print_function

import os
import SimpleHTTPServer
import SocketServer
import threading

WEBSERVER_PORT = 80
WEBSERVER_DIRECTORY = '/data'


class Module(object):
    def __init__(self, boot):
        self._boot = boot

        if boot.is_wifi_enabled:
            print("Starting web server on port {}.".format(WEBSERVER_PORT))
            thread = threading.Thread(target=self._server)
            thread.daemon = True
            thread.start()

    def _server(self):
        """Server thread entry point."""
        os.chdir(WEBSERVER_DIRECTORY)
        httpd = SocketServer.TCPServer(
            ("", WEBSERVER_PORT),
            SimpleHTTPServer.SimpleHTTPRequestHandler
        )
        httpd.serve_forever()

    def process(self, modules):
        pass

    def shutdown(self, modules):
        """Shutdown module."""
        pass
