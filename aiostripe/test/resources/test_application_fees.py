import unittest

import aiostripe
from aiostripe.test.helper import StripeResourceTest


class ApplicationFeeTest(StripeResourceTest):
    async def test_list_application_fees(self):
        await aiostripe.ApplicationFee.list()

        self.requestor_mock.request.assert_called_with('get', '/v1/application_fees',
                                                       {})


class ApplicationFeeRefundTest(StripeResourceTest):
    async def test_fetch_refund(self):
        fee = aiostripe.ApplicationFee.construct_from({
            'id': 'fee_get_refund',
            'refunds': {
                'object': 'list',
                'url': '/v1/application_fees/fee_get_refund/refunds',
            }
        }, 'api_key')

        await fee.refunds.retrieve('ref_get')

        self.requestor_mock.request.assert_called_with('get', '/v1/application_fees/fee_get_refund/refunds/ref_get',
                                                       {}, None)

    async def test_list_refunds(self):
        fee = aiostripe.ApplicationFee.construct_from({
            'id': 'fee_get_refund',
            'refunds': {
                'object': 'list',
                'url': '/v1/application_fees/fee_get_refund/refunds',
            }
        }, 'api_key')

        await fee.refunds.list()

        self.requestor_mock.request.assert_called_with('get', '/v1/application_fees/fee_get_refund/refunds',
                                                       {}, None)

    async def test_update_refund(self):
        refund = aiostripe.resource.ApplicationFeeRefund.construct_from({
            'id': 'ref_update',
            'fee': 'fee_update',
            'metadata': {},
        }, 'api_key')
        refund.metadata['key'] = 'value'

        await refund.save()

        self.requestor_mock.request.assert_called_with('post', '/v1/application_fees/fee_update/refunds/ref_update',
                                                       {
                                                           'metadata': {
                                                               'key': 'value',
                                                           }
                                                       }, None)


if __name__ == '__main__':
    unittest.main()
