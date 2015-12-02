import unittest

from aiostripe.test.helper import StripeApiTestCase, MyUpdateable


class UpdateableAPIResourceTests(StripeApiTestCase):
    def setUp(self):
        super().setUp()

        self.mock_response({
            'thats': 'it'
        })

        self.obj = MyUpdateable.construct_from({
            'id': 'myid',
            'foo': 'bar',
            'baz': 'boz',
            'metadata': {
                'size': 'l',
                'score': 4,
                'height': 10
            }
        }, 'mykey')

    async def checkSave(self):
        self.assertTrue(self.obj is await self.obj.save())

        self.assertEqual('it', self.obj.thats)
        # TODO: Should we force id to be retained?
        # self.assertEqual('myid', obj.id)
        self.assertRaises(AttributeError, getattr, self.obj, 'baz')

    async def test_idempotent_save(self):
        self.obj.baz = 'updated'
        await self.obj.save(idempotency_key='foo')

        self.requestor_mock.request.assert_called_with('post', '/v1/myupdateables/myid',
                                                       {
                                                           'metadata': {},
                                                           'baz': 'updated',
                                                       }, {'Idempotency-Key': 'foo'})

    async def test_save(self):
        self.obj.baz = 'updated'
        self.obj.other = 'newval'
        self.obj.metadata.size = 'm'
        self.obj.metadata.info = 'a2'
        self.obj.metadata.height = None

        await self.checkSave()

        self.requestor_mock.request.assert_called_with('post', '/v1/myupdateables/myid',
                                                       {
                                                           'baz': 'updated',
                                                           'other': 'newval',
                                                           'metadata': {
                                                               'size': 'm',
                                                               'info': 'a2',
                                                               'height': '',
                                                           }
                                                       }, None)

    async def test_add_key_to_nested_object(self):
        acct = MyUpdateable.construct_from({
            'id': 'myid',
            'legal_entity': {
                'size': 'l',
                'score': 4,
                'height': 10
            }
        }, 'mykey')

        acct.legal_entity['first_name'] = 'bob'

        self.assertTrue(acct is await acct.save())

        self.requestor_mock.request.assert_called_with('post', '/v1/myupdateables/myid',
                                                       {
                                                           'legal_entity': {
                                                               'first_name': 'bob',
                                                           }
                                                       }, None)

    async def test_save_nothing(self):
        acct = MyUpdateable.construct_from({
            'id': 'myid',
            'metadata': {
                'key': 'value',
            }
        }, 'mykey')

        self.assertTrue(acct is await acct.save())
        self.requestor_mock.request.assert_not_called()

    async def test_replace_nested_object(self):
        acct = MyUpdateable.construct_from({
            'id': 'myid',
            'legal_entity': {
                'last_name': 'smith',
            }
        }, 'mykey')

        acct.legal_entity = {
            'first_name': 'bob',
        }

        self.assertTrue(acct is await acct.save())

        self.requestor_mock.request.assert_called_with('post', '/v1/myupdateables/myid',
                                                       {
                                                           'legal_entity': {
                                                               'first_name': 'bob',
                                                               'last_name': '',
                                                           }
                                                       }, None)

    async def test_array_setting(self):
        acct = MyUpdateable.construct_from({
            'id': 'myid',
            'legal_entity': {}
        }, 'mykey')

        acct.legal_entity.additional_owners = [{'first_name': 'Bob'}]

        self.assertTrue(acct is await acct.save())

        self.requestor_mock.request.assert_called_with('post', '/v1/myupdateables/myid',
                                                       {
                                                           'legal_entity': {
                                                               'additional_owners': [
                                                                   {'first_name': 'Bob'}
                                                               ]
                                                           }
                                                       }, None)

    async def test_array_none(self):
        acct = MyUpdateable.construct_from({
            'id': 'myid',
            'legal_entity': {
                'additional_owners': None,
            }
        }, 'mykey')

        acct.foo = 'bar'

        self.assertTrue(acct is await acct.save())

        self.requestor_mock.request.assert_called_with('post', '/v1/myupdateables/myid',
                                                       {
                                                           'foo': 'bar',
                                                           'legal_entity': {},
                                                       }, None)

    async def test_array_insertion(self):
        acct = MyUpdateable.construct_from({
            'id': 'myid',
            'legal_entity': {
                'additional_owners': []
            }
        }, 'mykey')

        acct.legal_entity.additional_owners.append({'first_name': 'Bob'})

        self.assertTrue(acct is await acct.save())

        self.requestor_mock.request.assert_called_with('post', '/v1/myupdateables/myid',
                                                       {
                                                           'legal_entity': {
                                                               'additional_owners': {
                                                                   '0': {'first_name': 'Bob'},
                                                               }
                                                           }
                                                       }, None)

    async def test_array_update(self):
        acct = MyUpdateable.construct_from({
            'id': 'myid',
            'legal_entity': {
                'additional_owners': [
                    {'first_name': 'Bob'},
                    {'first_name': 'Jane'}
                ]
            }
        }, 'mykey')

        acct.legal_entity.additional_owners[1].first_name = 'Janet'

        self.assertTrue(acct is await acct.save())

        self.requestor_mock.request.assert_called_with('post', '/v1/myupdateables/myid',
                                                       {
                                                           'legal_entity': {
                                                               'additional_owners': {
                                                                   '0': {},
                                                                   '1': {'first_name': 'Janet'}
                                                               }
                                                           }
                                                       }, None)

    async def test_array_noop(self):
        acct = MyUpdateable.construct_from({
            'id': 'myid',
            'legal_entity': {
                'additional_owners': [{'first_name': 'Bob'}]
            },
            'currencies_supported': ['usd', 'cad']
        }, 'mykey')

        self.assertTrue(acct is await acct.save())

        self.requestor_mock.request.assert_called_with('post', '/v1/myupdateables/myid',
                                                       {
                                                           'legal_entity': {'additional_owners': {'0': {}}}
                                                       }, None)

    async def test_hash_noop(self):
        acct = MyUpdateable.construct_from({
            'id': 'myid',
            'legal_entity': {
                'address': {'line1': '1 Two Three'}
            }
        }, 'mykey')

        self.assertTrue(acct is await acct.save())

        self.requestor_mock.request.assert_called_with('post', '/v1/myupdateables/myid',
                                                       {
                                                           'legal_entity': {
                                                               'address': {}
                                                           }
                                                       }, None)

    async def test_save_replace_metadata_with_number(self):
        self.obj.baz = 'updated'
        self.obj.other = 'newval'
        self.obj.metadata = 3

        await self.checkSave()

        self.requestor_mock.request.assert_called_with('post', '/v1/myupdateables/myid',
                                                       {
                                                           'baz': 'updated',
                                                           'other': 'newval',
                                                           'metadata': 3,
                                                       }, None)

    async def test_save_overwrite_metadata(self):
        self.obj.metadata = {}

        await self.checkSave()

        self.requestor_mock.request.assert_called_with('post', '/v1/myupdateables/myid',
                                                       {
                                                           'metadata': {
                                                               'size': '',
                                                               'score': '',
                                                               'height': '',
                                                           }
                                                       }, None)

    async def test_save_replace_metadata(self):
        self.obj.baz = 'updated'
        self.obj.other = 'newval'
        self.obj.metadata = {
            'size': 'm',
            'info': 'a2',
            'score': 4,
        }

        await self.checkSave()

        self.requestor_mock.request.assert_called_with('post', '/v1/myupdateables/myid',
                                                       {
                                                           'baz': 'updated',
                                                           'other': 'newval',
                                                           'metadata': {
                                                               'size': 'm',
                                                               'info': 'a2',
                                                               'height': '',
                                                               'score': 4,
                                                           }
                                                       }, None)

    async def test_save_update_metadata(self):
        self.obj.baz = 'updated'
        self.obj.other = 'newval'
        self.obj.metadata.update({
            'size': 'm',
            'info': 'a2',
            'score': 4,
        })

        await self.checkSave()

        self.requestor_mock.request.assert_called_with('post', '/v1/myupdateables/myid',
                                                       {
                                                           'baz': 'updated',
                                                           'other': 'newval',
                                                           'metadata': {
                                                               'size': 'm',
                                                               'info': 'a2',
                                                               'score': 4,
                                                           }
                                                       }, None)

if __name__ == '__main__':
    unittest.main()
