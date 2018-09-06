from collections import namedtuple
import asyncio
import sys

from parallel_future import ParallelFuture


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
        self.process = await asyncio.create_subprocess_exec(
            *self.eval.cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)

    async def stop(self):
        print(self.eval.quitcmd, end='')
        await self.write(self.eval.quitcmd)
        if self.pf:
            self.pf.cancel()
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
        self.pf = ParallelFuture(
            lambda : asyncio.ensure_future(
                self._read_line(self.process.stdout,
                                self.eval.prompt,
                                is_err=False)),
            lambda: asyncio.ensure_future(
                self._read_line(self.process.stderr,
                                self.eval.prompt,
                                is_err=True)))
        while True:
            async for x in self.pf.wait():
                yield x

    async def _read_line(self, stream, prompt, is_err):
        ''' read a line from stream

        it returns either it reads \n or it matches prompt
        '''

        line = ''
        while True:
            ch = (await stream.read(1)).decode()
            line += ch
            if ch == '\n':  # it reads a newline
                return False, is_err, line
            if line == prompt:  # or it reads a prompt, e.g. '>>>'
                return True, is_err, line

    async def print_until_idle(self):
        async for is_idle, _, line in self.readlines():
            print(line, end='')
            sys.stdout.flush()
            if is_idle:
                break
        self.pf.cancel()
