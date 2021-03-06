import asyncio
import builtins
import sys
import types

from coroutils.helpers import update_wrapper, to_exception
from uniondict import uniondict

_missing = object()


def aiter(obj, sentinel=_missing):
    if sentinel is not _missing:
        return aiter_sentinel(obj)

    # if async iterable, return itself
    if getattr(obj, '__aiter__', None) is not None:
        return obj

    # likely, sync iterable
    try:
        _iter = iter(obj)
    except TypeError as exc:
        raise TypeError('%r object is not async-iterable' % type(obj)) from exc
    else:
        @async_generator
        async def gen():
            while True:
                try:
                    value = next(_iter)
                except StopIteration as exc:
                    return exc.value
                else:
                    await async_yield(value)

        return gen()


async def anext(iterator, default=_missing):
    try:
        return await iterator.__anext__()
    except StopAsyncIteration as exc:
        if default is _missing:
            raise

        return default


class asyncgenerator(object):
    def __init__(self, func, args, kwargs, loop=None):
        self.__name__ = func.__name__
        self.__qualname__ = func.__qualname__

        self.__func = self.__wrap(func, args, kwargs)
        self.__coro = None
        self.__future = None

        # self.__inherited_excinfo = None
        self.__loop = loop

        self.__started = False
        self.__finished = False

        self.__queue_send = asyncio.Queue(maxsize=1)
        self.__queue_yield = asyncio.Queue(maxsize=1)

    def __wrap(self, func, args, kwargs):
        async def inner():
            try:
                value = await func(*args, **kwargs)
            except:
                exc = to_exception(*sys.exc_info())
            else:
                exc = StopAsyncIteration(value)

            self.__finished = True
            await self.__queue_yield.put((None, exc))

        return update_wrapper(inner, func)

    async def __send(self, arg, exc):
        if not self.__started:
            if arg is not None:
                raise TypeError("can't send non-None value to a just-started async generator")

            if exc is not None:
                self.__started = True
                self.__finished = True

                raise exc

            self.__started = True
            self.__coro = self.__func()
            self.__future = asyncio.ensure_future(self.__coro, loop=self.__loop)
        else:
            # self.__inherited_excinfo = None  # tracebacks prevent gc
            if self.__finished:
                if exc is not None:
                    raise exc

                raise StopAsyncIteration()

            await self.__queue_send.put((arg, exc))

        r_value, r_exc = await self.__queue_yield.get()

        if r_exc is not None:
            raise r_exc

        return r_value

    async def send(self, arg):
        return await self.__send(arg, None)

    async def throw(self, exc_type, exc_value=None, exc_tb=None):
        exc = to_exception(exc_type, exc_value, exc_tb)

        return await self.__send(None, exc)

    async def close(self):
        try:
            await self.throw(GeneratorExit)
        except (GeneratorExit, StopAsyncIteration):
            pass
        else:
            raise RuntimeError('async generator ignored GeneratorExit')

        if self.__coro is not None:
            self.__coro.close()

    async def __aiter__(self):
        return self

    async def __anext__(self):
        return await self.send(None)

    async def _agi_yield(self, *args):
        if len(args) == 1:
            args = args[0]
        elif len(args) == 0:
            args = None

        await self.__queue_yield.put((args, None))

        value, exc = await self.__queue_send.get()

        if exc is not None:
            raise exc

        return value

    async def _agi_yield_from(self, iterator):
        iterator = aiter(iterator)

        while True:
            try:
                await self._agi_yield(await anext(iterator))
            except StopAsyncIteration as exc:
                if exc.args:
                    return exc.args[0]

                return None

    def __get_state(self):
        if not self.__started:
            return 'pending'

        if self.__finished:
            return 'finished'

        return 'running'

    def __repr__(self):
        return '<asyncgenerator object %s at %#x (%s)>' % (self.__name__, id(self), self.__get_state())

    def __str__(self):
        return repr(self)


def asyncgeneratorfunction(func):
    def inner(*args, **kwargs):
        def async_yield(*args):
            return gen._agi_yield(*args)

        def async_yield_from(*args):
            return gen._agi_yield_from(*args)

        ns = uniondict(builtins.__dict__, func.__globals__)
        ns['async_yield'] = async_yield
        ns['async_yield_from'] = async_yield_from
        ns['__builtins__'] = builtins.__dict__

        hooked_func = types.FunctionType(func.__code__, ns, func.__name__, func.__defaults__, func.__closure__)
        hooked_func = update_wrapper(hooked_func, func)

        gen = asyncgenerator(hooked_func, args, kwargs)

        return gen

    return update_wrapper(inner, func)


async_generator = asyncgeneratorfunction


# late binding
@async_generator
async def aiter_sentinel(func, sentinel):
    while True:
        value = await func()
        if value == sentinel:
            return

        await async_yield(value)


__all__ = ['async_generator', 'aiter', 'anext']
