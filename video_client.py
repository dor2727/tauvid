import http.client
import socket
import time

SERVER_IP = socket.getaddrinfo("video.tau.ac.il", 80)[0][-1][0]

class VideoClient():
    def __init__(self, headers=None):
        self.conn = http.client.HTTPConnection(SERVER_IP)

        if headers == None:
            headers = dict()

        self.headers = headers
        self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        self.headers['Connection'] = 'keep-alive'

    def get(self, url):
        self.conn.request('GET', url, headers=self.headers)
        with self.conn.getresponse() as res:
            resp = res.read()
        return resp

    def post(self, url, body):
        self.conn.request('POST', url, body=body, headers=self.headers)
        with self.conn.getresponse() as res:
            resp = res.read()
        return resp

    def head(self, url):
        while True:
            try:
                self.conn.request('HEAD', url, headers={'Connection': 'keep-alive'})
                res = self.conn.getresponse()
                res.read()
                return res.status

            except (http.client.HTTPException, ConnectionError):
                time.sleep(0.01)
                continue
