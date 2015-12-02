import aiostripe
import asyncio
from coroutils import *

@async_generator
async def foo():
    await async_yield(1)
    await async_yield(2)
    await async_yield(3)
    # await async_yield_from()


async def tests():
    r = []
    async for x in foo():
        r.append(x)
    assert(r == [1, 2, 3])

    r = []
    async for x in aiter(aiter(foo())):
        r.append(x)
    assert(r == [1, 2, 3])

    g = foo()
    assert(await anext(g) == 1)
    assert(await anext(g) == 2)
    assert(await anext(g) == 3)
    # print(await anext(g)) # raises




asyncio.get_event_loop().run_until_complete(tests())
