import unittest

from coroutils import async_generator
from coroutils.async_test import AsyncTestCase


class AsyncGeneratorTests(AsyncTestCase):
    # async def test_yield(self):
    #     @async_generator
    #     async def func():
    #         await async_yield(1)
    #         await async_yield(2)
    #         await async_yield(3)
    #
    #     r = []
    #     async for x in func():
    #         r.append(x)
    #
    #     self.assertEqual(r, [1, 2, 3])
    #
    # async def test_send(self):
    #     sent = []
    #
    #     @async_generator
    #     async def func():
    #         sent.append(await async_yield(1))
    #         sent.append(await async_yield(2))
    #         sent.append(await async_yield(3))
    #
    #         return 'return'
    #
    #     gen = func()
    #     self.assertEqual(await gen.send(None), 1)
    #     self.assertEqual(await gen.send('first'), 2)
    #     self.assertEqual(await gen.send('second'), 3)
    #     self.assertEqual(sent, ['first', 'second'])
    #
    #     await gen.close()
    #
    # async def test_send_just_started(self):
    #     @async_generator
    #     async def func():
    #         await async_yield(42)
    #
    #     gen = func()
    #     await self.assertRaisesAsync(TypeError, gen.send, 'fail')
    #     self.assertEqual(await gen.send(None), 42)
    #     await gen.close()
    #
    # async def test_stop_iteration(self):
    #     @async_generator
    #     async def func():
    #         await async_yield(1)
    #         await async_yield(2)
    #         return 'zz'
    #
    #     gen = func()
    #     self.assertEqual(await gen.send(None), 1)
    #     self.assertEqual(await gen.send(None), 2)
    #     await self.assertRaisesAsync(StopAsyncIteration, gen.send, None)
    #
    # async def test_close(self):
    #     r = []
    #     @async_generator
    #     async def func():
    #         r.append(1)
    #         await async_yield()
    #         r.append(2)
    #         await async_yield()
    #         r.append(3)
    #         await async_yield()
    #         r.append(4)
    #
    #     gen = func()
    #     await gen.send(None)
    #     await gen.send(None)
    #     await gen.close()
    #     self.assertEqual(r, [1, 2])
    #
    # async def test_send_after_close(self):
    #     @async_generator
    #     async def func():
    #         await async_yield()
    #         await async_yield()
    #         await async_yield()
    #
    #     gen = func()
    #     await gen.send(None)
    #     await gen.send(None)
    #     await gen.close()
    #     await self.assertRaisesAsync(StopAsyncIteration, gen.send, None)
    #     await self.assertRaisesAsync(StopAsyncIteration, gen.send, None)
    #
    # async def test_return_value(self):
    #     @async_generator
    #     async def func():
    #         return 123
    #
    #     gen = func()
    #
    #     await self.assertRaisesRegexAsync(StopAsyncIteration, '^123$', gen.send, None)
    #
    # async def test_return_none(self):
    #     @async_generator
    #     async def func():
    #         return
    #
    #     gen = func()
    #
    #     await self.assertRaisesRegexAsync(StopAsyncIteration, '^None$', gen.send, None)

    async def test_throw_fresh(self):
        class FooException(Exception):
            pass

        @async_generator
        async def func():
            await async_yield(42)

        gen = func()

        await self.assertRaisesAsync(FooException, gen.throw, FooException)

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
            try:
                await async_yield(42)
            except FooException:
                caught = True

        gen = func()

        await gen.send(None)
        await gen.throw(FooException)
        self.assertTrue(caught)


class AsyncGeneratorDecorator(AsyncTestCase):
    pass


if __name__ == '__main__':
    unittest.main()
