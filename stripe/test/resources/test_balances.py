import stripe
from stripe.test.helper import StripeResourceTest, desync


class BalanceTest(StripeResourceTest):
    @desync
    async def test_retrieve_balance(self):
        await stripe.Balance.retrieve()

        self.requestor_mock.request.assert_called_with(
            'get',
            '/v1/balance',
            {},
            None
        )


class BalanceTransactionTest(StripeResourceTest):
    @desync
    async def test_list_balance_transactions(self):
        await stripe.BalanceTransaction.list()
        self.requestor_mock.request.assert_called_with(
            'get',
            '/v1/balance/history',
            {}
        )
