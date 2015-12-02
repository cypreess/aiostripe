import asyncio
import functools
import inspect
from unittest import TestCase
from unittest import mock


def deasyncify(coro, loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()

    def inner(*args, **kwargs):
        return loop.run_until_complete(coro(*args, **kwargs))

    return functools.update_wrapper(inner, coro)


class AsyncTestCaseMeta(type):
    def __new__(mcs, what, bases, ns):
        for attr, prop in ns.items():
            if not attr.startswith('test_'):
                continue

            if not inspect.iscoroutinefunction(prop):
                continue

            ns[attr] = deasyncify(prop)

        return super().__new__(mcs, what, bases, ns)


class AsyncTestCase(TestCase, metaclass=AsyncTestCaseMeta):
    async def assertRaisesAsync(self, exception, coro, *args, **kwargs):
        with self.assertRaises(exception):
            await coro(*args, **kwargs)

    async def assertRaisesRegexAsync(self, exception, regex, coro, *args, **kwargs):
        with self.assertRaisesRegex(exception, regex):
            await coro(*args, **kwargs)


class AwaitableMixin:
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


class Mock(mock.Mock):
    pass


class AsyncMock(AwaitableMixin, Mock):
    pass


__all__ = ['deasyncify', 'AsyncTestCaseMeta', 'Mock', 'AsyncMock']
