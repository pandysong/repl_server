import socketserver
import subprocess
import time
from fcntl import fcntl, F_GETFL, F_SETFL
from os import O_NONBLOCK, read
import sys

print('start ghci')
p = subprocess.Popen(['ghci'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
flags = fcntl(p.stdout, F_GETFL)  # get current p.stdout flags
fcntl(p.stdout, F_SETFL, flags | O_NONBLOCK)


def wait_for_idle():
    line = ''
    while True:
        result = p.stdout.read()
        if not result:
            continue
        line += result.decode()
        pos = line.find('\n')
        if pos > 0:
            print(line[:pos])
            line = line[pos+1:]
        if line == 'Prelude> ':
            print(line, end='')
            sys.stdout.flush()
            return True


wait_for_idle()


def write_cmd(cmd):
    print(cmd)
    p.stdin.write((cmd+'\n').encode())
    p.stdin.flush()
    wait_for_idle()


class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        # self.request is the TCP socket connected to the client
        data = self.request.recv(1024).strip()
        #print("{} wrote:".format(self.client_address[0]))
        # print(self.data)
        write_cmd(data.decode())
        # just send back the same data, but upper-cased
        # self.request.sendall(self.data.upper())


if __name__ == "__main__":
    HOST, PORT = "localhost", 9999

    # Create the server, binding to localhost on port 9999
    server = socketserver.TCPServer((HOST, PORT), MyTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    print('Server listening at port {}'.format(PORT))
    server.serve_forever()

    p.terminate()
