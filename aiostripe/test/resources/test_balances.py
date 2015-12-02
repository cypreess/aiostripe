import unittest

import aiostripe
from aiostripe.test.helper import StripeResourceTest


class BalanceTest(StripeResourceTest):
    async def test_retrieve_balance(self):
        await aiostripe.Balance.retrieve()

        self.requestor_mock.request.assert_called_with('get', '/v1/balance',
                                                       {}, None)


class BalanceTransactionTest(StripeResourceTest):
    async def test_list_balance_transactions(self):
        await aiostripe.BalanceTransaction.list()

        self.requestor_mock.request.assert_called_with('get', '/v1/balance/history',
                                                       {})


if __name__ == '__main__':
    unittest.main()
