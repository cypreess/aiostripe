from coroutils.generator import async_generator

_missing = object()


@async_generator
async def aiter_sentinel(func, sentinel):
    while True:
        value = await func()
        if value == sentinel:
            return

        await async_yield(value)
