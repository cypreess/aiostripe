import aiostripe
from aiostripe.test.helper import StripeResourceTest


class ReversalTest(StripeResourceTest):
    async def test_fetch_reversal(self):
        transfer = aiostripe.Charge.construct_from({
            'id': 'tr_get',
            'reversals': {
                'object': 'list',
                'url': '/v1/transfers/tr_get/reversals',
            }
        }, 'api_key')

        await transfer.reversals.retrieve('foo')

        self.requestor_mock.request.assert_called_with('get', '/v1/transfers/tr_get/reversals/foo',
                                                       {}, None)

    async def test_list_reversals(self):
        transfer = aiostripe.Charge.construct_from({
            'id': 'tr_list',
            'reversals': {
                'object': 'list',
                'url': '/v1/transfers/tr_list/reversals',
            }
        }, 'api_key')

        await transfer.reversals.list()

        self.requestor_mock.request.assert_called_with('get', '/v1/transfers/tr_list/reversals',
                                                       {}, None)

    async def test_update_transfer(self):
        reversal = aiostripe.resource.Reversal.construct_from({
            'id': 'rev_update',
            'transfer': 'tr_update',
            'metadata': {},
        }, 'api_key')
        reversal.metadata['key'] = 'value'

        await reversal.save()

        self.requestor_mock.request.assert_called_with('post', '/v1/transfers/tr_update/reversals/rev_update',
                                                       {
                                                           'metadata': {
                                                               'key': 'value',
                                                           }
                                                       }, None)
