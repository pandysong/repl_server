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
            while True:
                data = await reader.read(100)
                if not data:
                    break
                message = data.decode()
                addr = writer.get_extra_info('peername')

                message = await self.handler(message)
                writer.write(message.encode())
                await writer.drain()

            await asyncio.sleep(0.2)
            writer.close()
        return handle_tcp

    def start(self, host='localhost', port='9987'):
        coro = asyncio.start_server(self._handler(), host, port, loop=self.loop)
        self.server = self.loop.run_until_complete(coro)
        #print('Serving on {}'.format(self.server.sockets[0].getsockname()))

    def close(self):
        self.server.close()
        self.loop.run_until_complete(self.server.wait_closed())
