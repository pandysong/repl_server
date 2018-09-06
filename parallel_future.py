import asyncio


class ParallelFuture:
    ''' A container to manage the Parallel Futures

    Make it convienent to manage the parallel futures
    '''

    def __init__(self, *args):
        ''' args is a list of functions to create the future
        '''
        self.futures = [None] * len(args)
        self.future_creators = args
        self.pending = []

    def _re_ensure(self, pending):
        for i in range(len(self.futures)):
            if self.futures[i] not in pending:
                self.futures[i] = self.future_creators[i]()

    async def wait(self):
        '''coroutine, wait for any of the futures to be completed and
           yield the results for those done
        '''
        self._re_ensure(self.pending)
        done, self.pending = await asyncio.wait(self.futures,
                                                return_when=asyncio.FIRST_COMPLETED)
        for i in done:
            yield i.result()

    def cancel(self):
        result = [m.cancel()for m in self.futures]
        self.pending = []
        return all(result)
