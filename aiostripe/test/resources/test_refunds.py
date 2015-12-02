import unittest

import aiostripe
from aiostripe.test.helper import StripeResourceTest


class RefundTest(StripeResourceTest):
    async def test_create_refund(self):
        await aiostripe.Refund.create(charge='ch_foo')

        self.requestor_mock.request.assert_called_with('post', '/v1/refunds',
                                                       {'charge': 'ch_foo'}, None)

    async def test_fetch_refund(self):
        await aiostripe.Refund.retrieve('re_foo')

        self.requestor_mock.request.assert_called_with('get', '/v1/refunds/re_foo',
                                                       {}, None)

    async def test_list_refunds(self):
        await aiostripe.Refund.list(limit=3, charge='ch_foo')

        self.requestor_mock.request.assert_called_with('get', '/v1/refunds',
                                                       {'limit': 3, 'charge': 'ch_foo'})

    async def test_update_refund(self):
        refund = aiostripe.resource.Refund.construct_from({
            'id': 'ref_update',
            'charge': 'ch_update',
            'metadata': {},
        }, 'api_key')
        refund.metadata['key'] = 'value'

        await refund.save()

        self.requestor_mock.request.assert_called_with('post', '/v1/refunds/ref_update',
                                                       {
                                                           'metadata': {
                                                               'key': 'value',
                                                           }
                                                       }, None)


class ChargeRefundTest(StripeResourceTest):
    async def test_create_refund(self):
        charge = aiostripe.Charge.construct_from({
            'id': 'ch_foo',
            'refunds': {
                'object': 'list',
                'url': '/v1/charges/ch_foo/refunds',
            }
        }, 'api_key')

        await charge.refunds.create()

        self.requestor_mock.request.assert_called_with('post', '/v1/charges/ch_foo/refunds',
                                                       {}, None)

    async def test_non_recursive_save(self):
        charge = aiostripe.Charge.construct_from({
            'id': 'ch_nested_update',
            'customer': {
                'object': 'customer',
                'description': 'foo',
            },
            'refunds': {
                'object': 'list',
                'url': '/v1/charges/ch_foo/refunds',
                'data': [{
                    'id': 'ref_123',
                }],
            },
        }, 'api_key')

        charge.customer.description = 'bar'
        charge.refunds.has_more = True
        charge.refunds.data[0].description = 'bar'

        await charge.save()

        self.requestor_mock.request.assert_called_with('post', '/v1/charges/ch_nested_update/refunds',
                                                       {}, None)

        # self.requestor_mock.request.assert_not_called()

    async def test_fetch_refund(self):
        charge = aiostripe.Charge.construct_from({
            'id': 'ch_get_refund',
            'refunds': {
                'object': 'list',
                'url': '/v1/charges/ch_get_refund/refunds',
            }
        }, 'api_key')

        await charge.refunds.retrieve('ref_get')

        self.requestor_mock.request.assert_called_with('get', '/v1/charges/ch_get_refund/refunds/ref_get',
                                                       {}, None)

    async def test_list_refunds(self):
        charge = aiostripe.Charge.construct_from({
            'id': 'ch_get_refund',
            'refunds': {
                'object': 'list',
                'url': '/v1/charges/ch_get_refund/refunds',
            }
        }, 'api_key')

        await charge.refunds.list()

        self.requestor_mock.request.assert_called_with('get', '/v1/charges/ch_get_refund/refunds',
                                                       {}, None)

    async def test_update_refund(self):
        refund = aiostripe.resource.Refund.construct_from({
            'id': 'ref_update',
            'charge': 'ch_update',
            'metadata': {},
        }, 'api_key')
        refund.metadata['key'] = 'value'
        await refund.save()

        self.requestor_mock.request.assert_called_with('post', '/v1/refunds/ref_update',
                                                       {
                                                           'metadata': {
                                                               'key': 'value',
                                                           }
                                                       }, None)


if __name__ == '__main__':
    unittest.main()
