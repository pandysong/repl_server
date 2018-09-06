import asyncio


class ReplTcpServer:
    '''Async Repl TcpServer

    Received data like ['1','show 1'] and feedback the result
    '''

    def __init__(self, loop, handler):
        ''' handler is a function which get data and return result
        '''
        self.loop = loop
        self.handler = handler

    def _handler(self):
        async def handle_tcp(reader, writer):
            data = await reader.read(100)
            message = data.decode()
            addr = writer.get_extra_info('peername')
            #print("Received %r from %r" % (message, addr))

            message = await self.handler(message)
            #print("Send: %r" % message)
            writer.write(message.encode())
            await writer.drain()

            #print("Close the client socket")
            writer.close()
        return handle_tcp

    def start(self, host='localhost', port='9987'):
        coro = asyncio.start_server(self._handler(), host, port, loop=self.loop)
        self.server = self.loop.run_until_complete(coro)
        #print('Serving on {}'.format(self.server.sockets[0].getsockname()))

    def close(self):
        self.server.close()
        self.loop.run_until_complete(self.server.wait_closed())
