import sys
import unittest

from coroutils import async_generator, anext, aiter
from coroutils.async_test import AsyncTestCase


class AsyncGeneratorTest(AsyncTestCase):
    async def test_name(self):
        @async_generator
        async def func():
            await async_yield(1)

        # check generator names
        gen = func()
        self.assertEqual(gen.__name__, "func")
        self.assertEqual(gen.__qualname__, "AsyncGeneratorTest.test_name.<locals>.func")

        # modify generator names
        gen.__name__ = "name"
        gen.__qualname__ = "qualname"
        self.assertEqual(gen.__name__, "name")
        self.assertEqual(gen.__qualname__, "qualname")

    async def test_yield(self):
        @async_generator
        async def func():
            await async_yield(1)
            await async_yield(2)
            await async_yield(3)

        r = []
        async for x in func():
            r.append(x)

        self.assertEqual(r, [1, 2, 3])

    async def test_send(self):
        sent = []

        @async_generator
        async def func():
            sent.append(await async_yield(1))
            sent.append(await async_yield(2))
            sent.append(await async_yield(3))

            return 'return'

        gen = func()
        self.assertEqual(await gen.send(None), 1)
        self.assertEqual(await gen.send('first'), 2)
        self.assertEqual(await gen.send('second'), 3)
        self.assertEqual(sent, ['first', 'second'])

        await gen.close()

    async def test_send_just_started(self):
        @async_generator
        async def func():
            await async_yield(42)

        gen = func()
        await self.assertRaisesAsync(TypeError, gen.send, 'fail')
        self.assertEqual(await gen.send(None), 42)
        await gen.close()

    async def test_stop_iteration(self):
        @async_generator
        async def func():
            await async_yield(1)
            await async_yield(2)
            return 'zz'

        gen = func()
        self.assertEqual(await gen.send(None), 1)
        self.assertEqual(await gen.send(None), 2)
        await self.assertRaisesAsync(StopAsyncIteration, gen.send, None)

    async def test_close(self):
        r = []

        @async_generator
        async def func():
            r.append(1)
            await async_yield()
            r.append(2)
            await async_yield()
            r.append(3)
            await async_yield()
            r.append(4)

        gen = func()
        await gen.send(None)
        await gen.send(None)
        await gen.close()
        self.assertEqual(r, [1, 2])

    async def test_send_after_close(self):
        @async_generator
        async def func():
            await async_yield()
            await async_yield()
            await async_yield()

        gen = func()
        await gen.send(None)
        await gen.send(None)
        await gen.close()
        await self.assertRaisesAsync(StopAsyncIteration, gen.send, None)
        await self.assertRaisesAsync(StopAsyncIteration, gen.send, None)

    async def test_return_value(self):
        @async_generator
        async def func():
            return 123

        gen = func()

        await self.assertRaisesRegexAsync(StopAsyncIteration, '^123$', gen.send, None)

    async def test_return_none(self):
        @async_generator
        async def func():
            return

        gen = func()

        await self.assertRaisesRegexAsync(StopAsyncIteration, '^None$', gen.send, None)

    async def test_throw_fresh(self):
        class FooException(Exception):
            pass

        @async_generator
        async def func():
            await async_yield(42)

        gen = func()

        await self.assertRaisesAsync(FooException, gen.throw, FooException)
        await self.assertRaisesAsync(StopAsyncIteration, gen.send, None)

    async def test_throw_running(self):
        class FooException(Exception):
            pass

        @async_generator
        async def func():
            await async_yield(42)
            await async_yield(10)

        gen = func()

        self.assertEqual(await gen.send(None), 42)
        await self.assertRaisesAsync(FooException, gen.throw, FooException)

    async def test_catch(self):
        class FooException(Exception):
            pass

        caught = False

        @async_generator
        async def func():
            nonlocal caught
            try:
                await async_yield(42)
            except FooException:
                caught = True

        gen = func()

        await gen.send(None)
        await self.assertRaisesAsync(StopAsyncIteration, gen.throw, FooException)
        self.assertTrue(caught)

    async def test_catch_rethrow(self):
        class FooException(Exception):
            pass

        class BarException(Exception):
            pass

        caught = False

        @async_generator
        async def func():
            nonlocal caught
            try:
                await async_yield(42)
            except FooException:
                caught = True
                raise BarException()

        gen = func()

        await gen.send(None)
        await self.assertRaisesAsync(BarException, gen.throw, FooException)
        self.assertTrue(caught)

    async def test_catch_recover(self):
        class FooException(Exception):
            pass

        caught = False

        @async_generator
        async def func():
            nonlocal caught
            try:
                await async_yield(42)
            except FooException:
                caught = True
            await async_yield('top kek')

        gen = func()

        await gen.send(None)
        self.assertEqual(await gen.throw(FooException), 'top kek')
        self.assertTrue(caught)
        await gen.close()

    async def test_except_throw(self):
        @async_generator
        async def store_raise_exc_generator():
            try:
                self.assertEqual(sys.exc_info()[0], None)
                await async_yield()
            except Exception as exc:
                # exception raised by gen.throw(exc)
                self.assertEqual(sys.exc_info()[0], ValueError)
                self.assertIsNone(exc.__context__)
                await async_yield()

                # ensure that the exception is not lost
                self.assertEqual(sys.exc_info()[0], ValueError)
                await async_yield()

                # we should be able to raise back the ValueError
                raise

        make = store_raise_exc_generator()
        await anext(make)

        try:
            raise ValueError()
        except Exception as exc:
            try:
                await make.throw(exc)
            except Exception:
                pass

        await anext(make)
        with self.assertRaises(ValueError) as cm:
            await anext(make)
        self.assertIsNone(cm.exception.__context__)

        self.assertEqual(sys.exc_info(), (None, None, None))

    async def test_iteration(self):
        @async_generator
        async def gen():
            for x in range(5):
                await async_yield(x)

        r = []
        async for x in gen():
            r.append(x)

        self.assertEqual(r, [0, 1, 2, 3, 4])

    async def test_yield_from(self):
        @async_generator
        async def foo(start, end):
            for x in range(start, end + 1):
                await async_yield(x)

        @async_generator
        async def bar():
            await async_yield_from(foo(10, 13))
            await async_yield_from(foo(1, 3))

        r = []
        async for x in bar():
            r.append(x)

        self.assertEqual(r, [10, 11, 12, 13, 1, 2, 3])

    async def test_yield_from_sync(self):
        @async_generator
        async def foo(start, end):
            for x in range(start, end + 1):
                await async_yield(x)

        @async_generator
        async def bar():
            await async_yield_from(range(10, 14))
            await async_yield_from(foo(1, 3))

        r = []
        async for x in bar():
            r.append(x)

        self.assertEqual(r, [10, 11, 12, 13, 1, 2, 3])

    async def test_yield_from_aiter(self):
        @async_generator
        async def foo(start, end):
            for x in range(start, end + 1):
                await async_yield(x)

        @async_generator
        async def bar():
            await async_yield_from(aiter(range(10, 14)))
            await async_yield_from(aiter(foo(20, 23)))
            await async_yield_from(foo(1, 3))
            await async_yield_from(aiter(aiter(aiter(aiter(aiter(['a', 'z']))))))

        r = []
        async for x in bar():
            r.append(x)

        self.assertEqual(r, [10, 11, 12, 13, 20, 21, 22, 23, 1, 2, 3, 'a', 'z'])


class AsyncGeneratorDecorator(AsyncTestCase):
    async def test_resolves_builtins(self):
        @async_generator
        async def func():
            import sys
            await async_yield(sys)

        import sys
        gen = func()
        async for x in gen:
            self.assertEqual(sys, x)


if __name__ == '__main__':
    unittest.main()
