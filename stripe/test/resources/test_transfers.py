import stripe
from stripe.test.helper import StripeResourceTest


class TransferTest(StripeResourceTest):
    async def test_list_transfers(self):
        await stripe.Transfer.list()
        self.requestor_mock.request.assert_called_with(
            'get',
            '/v1/transfers',
            {}
        )

    async def test_cancel_transfer(self):
        transfer = stripe.Transfer(id='tr_cancel')
        await transfer.cancel()

        self.requestor_mock.request.assert_called_with(
            'post',
            '/v1/transfers/tr_cancel/cancel',
            {},
            None
        )
