import asyncio
from repl_tcp_server import ReplTcpServer
import repl

loop = asyncio.get_event_loop()

r = repl.Repl(loop, 'haskell')
r.start()


async def run_cmd(r, cmd):
    print(cmd, end='')
    await r.write(cmd)
    await r.print_until_idle()
    return "success"


async def repl_eval(data):
    ''' process the message

    data is a string [linenumber, 'line']
    '''
    #cmd = eval(data)
    cmd = data
    return await run_cmd(r, cmd)


svr = ReplTcpServer(loop, repl_eval)
svr.start()
# Serve requests until Ctrl+C is pressed
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

svr.close()
r.close()
loop.close()
