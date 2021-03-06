import unittest

import aiostripe
from aiostripe.test.helper import StripeResourceTest


class AccountTest(StripeResourceTest):
    async def test_retrieve_account_deprecated(self):
        await aiostripe.Account.retrieve()

        self.requestor_mock.request.assert_called_with('get', '/v1/account',
                                                       {}, None)

    async def test_retrieve_account(self):
        await aiostripe.Account.retrieve('acct_foo')

        self.requestor_mock.request.assert_called_with('get', '/v1/accounts/acct_foo',
                                                       {}, None)

    async def test_list_accounts(self):
        await aiostripe.Account.list()

        self.requestor_mock.request.assert_called_with('get', '/v1/accounts',
                                                       {})

    async def test_create_account(self):
        pii = {
            'type': 'individual',
            'first_name': 'Joe',
            'last_name': 'Smith',
        }

        await aiostripe.Account.create(legal_entity=pii)

        self.requestor_mock.request.assert_called_with('post', '/v1/accounts',
                                                       {
                                                           'legal_entity': pii,
                                                       }, None)

    async def test_update_account(self):
        acct = aiostripe.Account.construct_from({
            'id': 'acct_update',
            'legal_entity': {'first_name': 'Joe'},
        }, 'api_key')
        acct.legal_entity['first_name'] = 'Bob'

        await acct.save()

        self.requestor_mock.request.assert_called_with('post', '/v1/accounts/acct_update',
                                                       {
                                                           'legal_entity': {
                                                               'first_name': 'Bob',
                                                           },
                                                       }, None)

    async def test_account_delete_bank_account(self):
        source = aiostripe.BankAccount.construct_from({
            'account': 'acc_delete_ba',
            'id': 'ba_delete_ba',
        }, 'api_key')

        await source.delete()

        self.requestor_mock.request.assert_called_with('delete',
                                                       '/v1/accounts/acc_delete_ba/external_accounts/ba_delete_ba',
                                                       {}, None)

    async def test_verify_additional_owner(self):
        acct = aiostripe.Account.construct_from({
            'id': 'acct_update',
            'additional_owners': [{
                'first_name': 'Alice',
                'verification': {},
            }]
        }, 'api_key')
        owner = acct.additional_owners[0]
        owner.verification.document = 'file_foo'

        await acct.save()

        self.requestor_mock.request.assert_called_with('post', '/v1/accounts/acct_update',
                                                       {
                                                           'additional_owners': {
                                                               '0': {
                                                                   'verification': {
                                                                       'document': 'file_foo',
                                                                   },
                                                               },
                                                           },
                                                       }, None)


if __name__ == '__main__':
    unittest.main()
