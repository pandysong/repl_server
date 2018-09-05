from collections import namedtuple
import asyncio
import sys


class Repl:
    '''Repl is a Python Wrapper over the evaluator

    It could be controller by read() and write() interface.
    '''

    Evaluator = namedtuple('Eval', 'cmd prompt quitcmd')
    _EVALS = {
        'python': Evaluator(['python'], '>>> ', 'quit()\n'),
        'python3': Evaluator(['python3'], '>>> ', 'quit()\n'),
        'haskell':  Evaluator(['ghci'], 'Prelude> ', ':quit\n'),
    }

    def __init__(self, lang):
        '''Repl with specific language

        `lang` could be 'python','haskell', etc.
        '''
        self.eval = self._EVALS.get(lang.lower())
        if not self.eval:
            raise TypeError('{} not supported'.format(lang))

    async def start(self):
        self.process = await asyncio.create_subprocess_exec(*self.eval.cmd,
                                                            stdin=asyncio.subprocess.PIPE,
                                                            stdout=asyncio.subprocess.PIPE,
                                                            stderr=asyncio.subprocess.PIPE)

    async def stop(self):
        print(self.eval.quitcmd, end='')
        await self.write(self.eval.quitcmd)
        self.std_f.cancel()
        self.err_f.cancel()
        re = await self.process.communicate()
        for i in re:
            print(i.decode(), end='')

    async def write(self, line):
        self.process.stdin.write(line.encode())
        await self.process.stdin.drain()

    async def readlines(self):
        '''generator to yield the lines

        It will yield either it reads \n or it matches the prompt, e.g. '>>> '
        it return a tuple, the first parameter indicates it is error or not
        '''
        def std_future():
            return asyncio.ensure_future(self._read_line(self.process.stdout,
                                                         self.eval.prompt,
                                                         is_err=False))

        def err_future():
            return asyncio.ensure_future(self._read_line(self.process.stderr,
                                                         self.eval.prompt,
                                                         is_err=True))
        self.std_f, self.err_f = None, None

        def new_future(pending):
            if self.std_f not in pending:
                self.std_f = std_future()
            if self.err_f not in pending:
                self.err_f = err_future()
            return set([self.std_f, self.err_f])

        pending = set()

        while True:
            pending = new_future(pending)
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            for i in done:
                yield i.result()

    async def _read_line(self, stream, prompt, is_err):
        ''' read a line from stream

        it returns either it reads \n or it matches prompt
        '''

        line = ''
        while True:
            ch = await stream.read(1)  # unbuffered reading
            ch = ch.decode()
            line += ch
            if ch == '\n':  # it reads a newline
                return False, is_err, line
            if line == prompt:  # or it reads a prompt, e.g. '>>>'
                return True, is_err, line

    async def print_until_idle(self):
        async for is_idle, _, line in repl.readlines():
            print(line, end='')
            sys.stdout.flush()
            if is_idle:
                break
        self.std_f.cancel()
        self.err_f.cancel()


async def run_cmd(repl, cmd):
    print(cmd, end='')
    await repl.write(cmd)
    await repl.print_until_idle()


async def server_lines(repl):
    await repl.start()
    await repl.print_until_idle()
    await run_cmd(repl, '1+2\n')
    await run_cmd(repl, 'show 12342\n')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    repl = Repl('haskell')
    try:
        loop.run_until_complete(server_lines(repl))
    except KeyboardInterrupt as e:
        pass

    loop.run_until_complete(repl.stop())
    loop.close()
