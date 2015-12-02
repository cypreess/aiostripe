import unittest

import aiostripe
from aiostripe.test.helper import StripeResourceTest


class MetadataTest(StripeResourceTest):
    async def test_noop_metadata(self):
        charge = aiostripe.Charge(id='ch_foo')
        charge.description = 'test'

        await charge.save()

        self.requestor_mock.request.assert_called_with('post', '/v1/charges/ch_foo',
                                                       {
                                                           'description': 'test',
                                                       }, None)

    async def test_unset_metadata(self):
        charge = aiostripe.Charge(id='ch_foo')
        charge.metadata = {}

        await charge.save()

        self.requestor_mock.request.assert_called_with('post', '/v1/charges/ch_foo',
                                                       {
                                                           'metadata': {},
                                                       }, None)

    async def test_whole_update(self):
        charge = aiostripe.Charge(id='ch_foo')
        charge.metadata = {'whole': 'update'}

        await charge.save()

        self.requestor_mock.request.assert_called_with('post', '/v1/charges/ch_foo',
                                                       {
                                                           'metadata': {'whole': 'update'},
                                                       }, None)

    async def test_individual_delete(self):
        charge = aiostripe.Charge(id='ch_foo')
        charge.metadata = {'whole': None}
        await charge.save()

        self.requestor_mock.request.assert_called_with('post', '/v1/charges/ch_foo',
                                                       {
                                                           'metadata': {'whole': None},
                                                       }, None)


if __name__ == '__main__':
    unittest.main()
