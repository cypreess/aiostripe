import operator
import unittest
from decimal import Decimal
from fractions import Fraction

from coroutils.async_test import AsyncTestCase
from coroutils.funcs import *

async def LIST(it):
    return list(await aitersync(it))


class TestBasicOps(AsyncTestCase):
    async def test_accumulate(self):
        self.assertEqual(await LIST(aaccumulate(arange(10))),  # one positional arg
                         [0, 1, 3, 6, 10, 15, 21, 28, 36, 45])
        self.assertEqual(await LIST(aaccumulate(iterable=range(10))),  # kw arg
                         [0, 1, 3, 6, 10, 15, 21, 28, 36, 45])
        for typ in int, complex, Decimal, Fraction:  # multiple types
            self.assertEqual(
                await LIST(aaccumulate(map(typ, range(10)))),
                await LIST(map(typ, [0, 1, 3, 6, 10, 15, 21, 28, 36, 45])))
        self.assertEqual(await LIST(aaccumulate('abc')),
                         ['a', 'ab', 'abc'])  # works with non-numeric
        self.assertEqual(await LIST(aaccumulate([])),
                         [])  # empty iterable
        self.assertEqual(await LIST(aaccumulate([7])),
                         [7])  # iterable of length one
        await self.assertRaisesAsync(TypeError, aaccumulate, range(10), 5, 6)  # too many args
        await self.assertRaisesAsync(TypeError, aaccumulate)  # too few args
        await self.assertRaisesAsync(TypeError, aaccumulate, x=range(10))  # unexpected kwd arg
        # await self.assertRaisesAsync(TypeError, LIST, aaccumulate([1, []]))  # args that don't add

        s = [2, 8, 9, 5, 7, 0, 3, 4, 1, 6]
        self.assertEqual(await LIST(aaccumulate(s, min)),
                         [2, 2, 2, 2, 2, 0, 0, 0, 0, 0])
        self.assertEqual(await LIST(aaccumulate(s, max)),
                         [2, 8, 9, 9, 9, 9, 9, 9, 9, 9])
        self.assertEqual(await LIST(aaccumulate(s, operator.mul)),
                         [2, 16, 144, 720, 5040, 0, 0, 0, 0, 0])
        # with self.assertRaises(TypeError):
        #     await LIST(aaccumulate(s, chr))  # unary-operation


# TODO: get tests from test_itertools.py and port them

if __name__ == '__main__':
    unittest.main()
