import unittest

import aiostripe
from aiostripe.test.helper import StripeApiTestCase


class ListObjectTests(StripeApiTestCase):
    def setUp(self):
        super().setUp()

        self.lo = aiostripe.resource.ListObject.construct_from({
            'id': 'me',
            'url': '/my/path',
            'data': ['foo'],
        }, 'mykey')

        self.mock_response([{
            'object': 'charge',
            'foo': 'bar',
        }])

    def assertResponse(self, res):
        self.assertTrue(isinstance(res[0], aiostripe.Charge))
        self.assertEqual('bar', res[0].foo)

    async def test_for_loop(self):
        seen = []

        for item in self.lo:
            seen.append(item)

        self.assertEqual(['foo'], seen)

    async def test_list(self):
        res = await self.lo.list(myparam='you')

        self.requestor_mock.request.assert_called_with('get', '/my/path',
                                                       {'myparam': 'you'}, None)

        self.assertResponse(res)

    async def test_create(self):
        res = await self.lo.create(myparam='eter')

        self.requestor_mock.request.assert_called_with('post', '/my/path',
                                                       {'myparam': 'eter'}, None)

        self.assertResponse(res)

    async def test_retrieve(self):
        res = await self.lo.retrieve('myid', myparam='cow')

        self.requestor_mock.request.assert_called_with('get', '/my/path/myid',
                                                       {'myparam': 'cow'}, None)

        self.assertResponse(res)


class AutoPagingTests(StripeApiTestCase):
    async def test_iter_one_page(self):
        lo = aiostripe.resource.ListObject.construct_from({
            'object': 'list',
            'url': '/my/path',
            'data': [{'id': 'foo'}],
        }, 'mykey')

        self.requestor_mock.request.assert_not_called()

        seen = []
        async for item in lo.auto_paging_iter():
            seen.append(item['id'])

        self.assertEqual(['foo'], seen)

    async def test_iter_two_pages(self):
        lo = aiostripe.resource.ListObject.construct_from({
            'object': 'list',
            'url': '/my/path',
            'has_more': True,
            'data': [{'id': 'foo'}],
        }, 'mykey')

        self.mock_response({
            'object': 'list',
            'data': [{'id': 'bar'}],
            'url': '/my/path',
            'has_more': False,
        })

        seen = []
        async for item in lo.auto_paging_iter():
            seen.append(item['id'])

        self.requestor_mock.request.assert_called_with('get', '/my/path',
                                                       {'starting_after': 'foo'}, None)

        self.assertEqual(['foo', 'bar'], seen)

    async def test_class_method_two_pages(self):
        self.mock_response({
            'object': 'list',
            'data': [{'id': 'bar'}],
            'url': '/v1/charges',
            'has_more': False,
        })

        seen = []
        async for i in aiostripe.Charge.auto_paging_iter(limit=25):
            seen.append(i['id'])

        self.requestor_mock.request.assert_called_with('get', '/v1/charges',
                                                       {'limit': 25})

        self.assertEqual(['bar'], seen)


if __name__ == '__main__':
    unittest.main()
