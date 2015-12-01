import aiostripe
from aiostripe.test.helper import StripeResourceTest


class BitcoinReceiverTest(StripeResourceTest):
    async def test_retrieve_resource(self):
        await aiostripe.BitcoinReceiver.retrieve('btcrcv_test_receiver')

        self.requestor_mock.request.assert_called_with('get', '/v1/bitcoin/receivers/btcrcv_test_receiver',
                                                       {}, None)

    async def test_list_receivers(self):
        await aiostripe.BitcoinReceiver.list()

        self.requestor_mock.request.assert_called_with('get', '/v1/bitcoin/receivers',
                                                       {})

    async def test_create_receiver(self):
        await aiostripe.BitcoinReceiver.create(amount=100, description='some details', currency='usd',
                                               email='do+fill_now@stripe.com')

        self.requestor_mock.request.assert_called_with('post', '/v1/bitcoin/receivers',
                                                       {
                                                           'amount': 100,
                                                           'description': 'some details',
                                                           'currency': 'usd',
                                                           'email': 'do+fill_now@stripe.com'
                                                       }, None)

    async def test_update_receiver_without_customer(self):
        params = {
            'id': 'receiver',
            'amount': 100,
            'description': 'some details',
            'currency': 'usd'
        }
        r = aiostripe.BitcoinReceiver.construct_from(params, 'api_key')
        r.description = 'some other details'

        await r.save()

        self.requestor_mock.request.assert_called_with('post', '/v1/bitcoin/receivers/receiver',
                                                       {
                                                           'description': 'some other details'
                                                       }, None)

    async def test_update_receiver_with_customer(self):
        params = {'id': 'receiver',
                  'amount': 100,
                  'description': 'some details',
                  'currency': 'usd',
                  'customer': 'cust'}
        r = aiostripe.BitcoinReceiver.construct_from(params, 'api_key')
        r.description = 'some other details'

        await r.save()

        self.requestor_mock.request.assert_called_with('post', '/v1/customers/cust/sources/receiver',
                                                       {
                                                           'description': 'some other details',
                                                       }, None)

    async def test_delete_receiver_without_customer(self):
        params = {
            'id': 'receiver',
            'amount': 100,
            'description': 'some details',
            'currency': 'usd'
        }
        r = aiostripe.BitcoinReceiver.construct_from(params, 'api_key')

        await r.delete()

        self.requestor_mock.request.assert_called_with('delete', '/v1/bitcoin/receivers/receiver',
                                                       {}, None)

    async def test_delete_receiver_with_customer(self):
        params = {
            'id': 'receiver',
            'amount': 100,
            'description': 'some details',
            'currency': 'usd',
            'customer': 'cust'
        }
        r = aiostripe.BitcoinReceiver.construct_from(params, 'api_key')

        await r.delete()

        self.requestor_mock.request.assert_called_with('delete', '/v1/customers/cust/sources/receiver',
                                                       {}, None)

    async def test_list_transactions(self):
        receiver = aiostripe.BitcoinReceiver.construct_from({
            'id': 'btcrcv_foo',
            'transactions': {
                'object': 'list',
                'url': '/v1/bitcoin/receivers/btcrcv_foo/transactions',
            }
        }, 'api_key')

        await receiver.transactions.list()

        self.requestor_mock.request.assert_called_with('get', '/v1/bitcoin/receivers/btcrcv_foo/transactions',
                                                       {}, None)
