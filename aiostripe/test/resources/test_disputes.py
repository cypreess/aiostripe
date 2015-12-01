import aiostripe
from aiostripe.test.helper import StripeResourceTest, DUMMY_DISPUTE, NOW


class DisputeTest(StripeResourceTest):
    async def test_list_all_disputes(self):
        await aiostripe.Dispute.list(created={'lt': NOW})

        self.requestor_mock.request.assert_called_with('get', '/v1/disputes',
                                                       {
                                                           'created': {'lt': NOW},
                                                       })

    async def test_create_dispute(self):
        await aiostripe.Dispute.create(idempotency_key='foo', **DUMMY_DISPUTE)

        self.requestor_mock.request.assert_called_with('post', '/v1/disputes',
                                                       DUMMY_DISPUTE, {'Idempotency-Key': 'foo'})

    async def test_retrieve_dispute(self):
        await aiostripe.Dispute.retrieve('dp_test_id')

        self.requestor_mock.request.assert_called_with('get', '/v1/disputes/dp_test_id',
                                                       {}, None)

    async def test_update_dispute(self):
        dispute = aiostripe.Dispute.construct_from({
            'id': 'dp_update_id',
            'evidence': {
                'product_description': 'description',
            },
        }, 'api_key')
        dispute.evidence['customer_name'] = 'customer'
        dispute.evidence['uncategorized_text'] = 'text'

        await dispute.save()

        self.requestor_mock.request.assert_called_with('post', '/v1/disputes/dp_update_id',
                                                       {
                                                           'evidence': {
                                                               'customer_name': 'customer',
                                                               'uncategorized_text': 'text',
                                                           }
                                                       }, None)

    async def test_close_dispute(self):
        dispute = aiostripe.Dispute(id='dp_close_id')

        await dispute.close(idempotency_key='foo')

        self.requestor_mock.request.assert_called_with('post', '/v1/disputes/dp_close_id/close',
                                                       {}, {'Idempotency-Key': 'foo'})
