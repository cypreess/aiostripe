import collections
import operator
import sys
from functools import update_wrapper
from inspect import iscoroutinefunction

from coroutils.generator import async_generator, aiter, anext

_missing = object()


def wrapsync(func):
    """Turns synchronous function into asynchronous."""

    if iscoroutinefunction(func):
        return func

    async def inner(*args, **kwargs):
        return func(*args, **kwargs)

    return update_wrapper(inner, func)


async def aitersync(iterable):
    results = []

    async for x in aiter(iterable):
        results.append(x)

    return iter(results)


async def aall(iterable):
    async for element in aiter(iterable):
        if not element:
            return False
    return True


async def aany(iterable):
    async for element in aiter(iterable):
        if element:
            return True
    return False


@async_generator
async def aenumerate(sequence, start=0):
    n = start
    async for elem in aiter(sequence):
        await async_yield(n, elem)
        n += 1


@async_generator
async def afilter(function, iterable):
    if function is None:
        function = lambda x: x
    function = wrapsync(function)

    async for element in aiter(iterable):
        if await function(element):
            await async_yield(element)


@async_generator
async def afilterfalse(function, iterable):
    if function is None:
        function = lambda x: x
    function = wrapsync(function)

    async for element in aiter(iterable):
        if not await function(element):
            await async_yield(element)


@async_generator
async def amap(function, iterable, *args):
    function = wrapsync(function)

    iterables = (iterable, *args)
    async for args in azip(*iterables):
        await async_yield(await function(*args))


async def amax(iterable, key=None, default=_missing):
    if key is None:
        key = lambda x: x
    key = wrapsync(key)

    value = _missing
    kvalue = _missing

    async for x in aiter(iterable):
        kx = await key(x)

        if value is _missing:
            value = x
            kvalue = kx
        else:
            if kx > kvalue:
                value = x
                kvalue = kx

    if value is _missing:
        if default is not _missing:
            return default

        raise ValueError('amax() arg is an empty sequence')

    return value


async def amin(iterable, key=None, default=_missing):
    if key is None:
        key = lambda x: x
    key = wrapsync(key)

    value = _missing
    kvalue = _missing

    async for x in aiter(iterable):
        kx = await key(x)

        if value is _missing:
            value = x
            kvalue = kx
        else:
            if kx < kvalue:
                value = x
                kvalue = kx

    if value is _missing:
        if default is not _missing:
            return default

        raise ValueError('amin() arg is an empty sequence')

    return value


@async_generator
async def arange(*opts):
    return await async_yield_from(range(*opts))


async def areversed(seq):
    return aiter(reversed(await aitersync(seq)))


async def asorted(iterable, *args, **kwargs):
    return aiter(sorted(await aitersync(iterable), *args, **kwargs))


async def asum(iterable, start=0):
    async for x in aiter(iterable):
        start += x

    return start


@async_generator
async def azip(*iterables):
    # zip('ABCD', 'xy') --> Ax By
    sentinel = object()
    iterators = []
    for it in iterables:
        iterators.append(aiter(it))

    while iterators:
        result = []
        async for it in iterators:
            elem = await anext(it, sentinel)
            if elem is sentinel:
                return
            result.append(elem)

        await async_yield(tuple(result))


@async_generator
async def aaccumulate(iterable, func=None):
    'Return running totals'

    if func is None:
        func = operator.add
    func = wrapsync(func)

    # accumulate([1,2,3,4,5]) --> 1 3 6 10 15
    # accumulate([1,2,3,4,5], operator.mul) --> 1 2 6 24 120
    it = aiter(iterable)
    try:
        total = await anext(it)
    except StopAsyncIteration:
        return
    await async_yield(total)
    async for element in it:
        total = await func(total, element)
        await async_yield(total)


@async_generator
async def achain(*iterables):
    # chain('ABC', 'DEF') --> A B C D E F
    for it in iterables:
        async for element in aiter(it):
            await async_yield(element)


@async_generator
async def afrom_iterable(iterables):
    # chain.from_iterable(['ABC', 'DEF']) --> A B C D E F
    async for it in aiter(iterables):
        async for element in aiter(it):
            await async_yield(element)


@async_generator
async def acompress(data, selectors):
    # compress('ABCDEF', [1,0,1,0,1,1]) --> A C E F
    async for d, s in azip(data, selectors):
        if s:
            await async_yield(d)


@async_generator
async def acount(start=0, step=1):
    # count(10) --> 10 11 12 13 14 ...
    # count(2.5, 0.5) -> 2.5 3.0 3.5 ...
    n = start
    while True:
        await async_yield(n)
        n += step


@async_generator
async def acycle(iterable):
    # cycle('ABCD') --> A B C D A B C D A B C D ...
    saved = []
    async for element in aiter(iterable):
        await async_yield(element)
        saved.append(element)
    while saved:
        for element in saved:
            await async_yield(element)


@async_generator
async def adropwhile(predicate, iterable):
    # dropwhile(lambda x: x<5, [1,4,6,4,1]) --> 6 4 1
    predicate = wrapsync(predicate)
    iterable = aiter(iterable)
    async for x in iterable:
        if not await predicate(x):
            await async_yield(x)
            break
    async for x in iterable:
        await async_yield(x)


@async_generator
async def aislice(iterable, *args):
    # islice('ABCDEFG', 2) --> A B
    # islice('ABCDEFG', 2, 4) --> C D
    # islice('ABCDEFG', 2, None) --> C D E F G
    # islice('ABCDEFG', 0, None, 2) --> A C E G
    s = slice(*args)
    it = iter(range(s.start or 0, s.stop or sys.maxsize, s.step or 1))
    try:
        nexti = next(it)
    except StopIteration:
        return
    async for i, element in aenumerate(iterable):
        if i == nexti:
            await async_yield(element)
            nexti = next(it)


@async_generator
async def arepeat(value, times=None):
    # repeat(10, 3) --> 10 10 10
    if times is None:
        while True:
            await async_yield(value)
    else:
        for i in range(times):
            await async_yield(value)


@async_generator
async def astarmap(function, iterable):
    # starmap(pow, [(2,5), (3,2), (10,3)]) --> 32 9 1000
    function = wrapsync(function)
    async for args in aiter(iterable):
        await async_yield(await function(*args))


@async_generator
async def atakewhile(predicate, iterable):
    predicate = wrapsync(predicate)
    # takewhile(lambda x: x<5, [1,4,6,4,1]) --> 1 4
    async for x in aiter(iterable):
        if await predicate(x):
            await async_yield(x)
        else:
            break


@async_generator
async def atee(iterable, n=2):
    it = aiter(iterable)
    deques = [collections.deque() for i in range(n)]

    async def gen(mydeque):
        while True:
            if not mydeque:  # when the local deque is empty
                try:
                    newval = await anext(it)  # fetch a new value and
                except StopAsyncIteration:
                    return
                for d in deques:  # load it to all the deques
                    d.append(newval)
            await async_yield(mydeque.popleft())

    res = []
    for d in deques:
        res.append(await gen(d))
    return tuple(res)


class AsyncZipExhausted(Exception):
    pass


@async_generator
async def azip_longest(*args, **kwds):
    # zip_longest('ABCD', 'xy', fillvalue='-') --> Ax By C- D-
    fillvalue = kwds.get('fillvalue')
    counter = len(args) - 1

    @async_generator
    async def sentinel():
        nonlocal counter
        if not counter:
            raise AsyncZipExhausted
        counter -= 1
        await async_yield(fillvalue)

    fillers = await arepeat(fillvalue)
    iterators = []
    for it in args:
        iterators.append(await achain(it, sentinel(), fillers))
    try:
        while iterators:
            await async_yield(tuple(await aitersync(amap(anext, iterators))))
    except AsyncZipExhausted:
        pass

__all__ = ['wrapsync', 'aitersync', 'aall', 'aany', 'aenumerate', 'afilter', 'afilterfalse', 'amap', 'amax', 'amin',
           'arange', 'areversed', 'asorted', 'asum', 'azip', 'aaccumulate', 'achain', 'afrom_iterable', 'acompress',
           'acount', 'acycle', 'adropwhile', 'aislice', 'arepeat', 'astarmap', 'atakewhile', 'atee', 'azip_longest']
