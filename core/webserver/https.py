import http.server
import socketserver
import socket

class vars:
    connectedClients = []

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.dir = "./modules/activeInjects"
        super().__init__(*args, directory=self.dir, **kwargs)
    def log_message(self, format, *args):
        return
    def handle_one_request(self):
        vars.connectedClients.append(self.client_address)
        return http.server.SimpleHTTPRequestHandler.handle_one_request(self)


class HTTPServer:
    connections = []
    def __init__(self, port: int = 80, directory: str = "/injects/"):
        self.port = port
        self.dir = directory

    def forever(self):
        with socketserver.TCPServer(("", self.port), Handler) as httpd:
            self.serve = httpd
            httpd.serve_forever()

    def getClients(self):
        return vars.connectedClients

    def shutdown(self):
        self.serve.shutdown()

class FakeHTTPServer:
    """
    an http server that recives connections, but doesnt send anything back: usually only for pulling ip addresses
    """
    connections = []
    def __init__(self, bindto:tuple=("0.0.0.0", "8888"), timeout=5):
        self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp.bind(bindto)
        self.tcp.settimeout(timeout)

    def waitFor(self):
        a = self.tcp.listen()
        b = self.tcp.accept()

        return (a,b)