import asyncio
import repl


async def run_cmd(r, cmd):
    print(cmd, end='')
    await r.write(cmd)
    await r.print_until_idle()


async def server_lines(r, loop):
    await r.start()
    await r.print_until_idle()
    await run_cmd(r, '1+2\n')
    await run_cmd(r, 'show 12342\n')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    r = repl.Repl('haskell')
    try:
        loop.run_until_complete(server_lines(r, loop))
    except KeyboardInterrupt as e:
        pass

    loop.run_until_complete(r.stop())
    loop.close()
