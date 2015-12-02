import unittest

import aiostripe
from aiostripe.test.helper import StripeResourceTest


class TransferTest(StripeResourceTest):
    async def test_list_transfers(self):
        await aiostripe.Transfer.list()

        self.requestor_mock.request.assert_called_with('get', '/v1/transfers', {})

    async def test_cancel_transfer(self):
        transfer = aiostripe.Transfer(id='tr_cancel')
        await transfer.cancel()

        self.requestor_mock.request.assert_called_with('post', '/v1/transfers/tr_cancel/cancel', {}, None)


if __name__ == '__main__':
    unittest.main()
