import unittest

from aiostripe.test.helper import StripeApiTestCase, MyDeletable


class DeletableAPIResourceTests(StripeApiTestCase):
    async def test_delete(self):
        self.mock_response({
            'id': 'mid',
            'deleted': True,
        })

        obj = MyDeletable.construct_from({
            'id': 'mid'
        }, 'mykey')

        self.assertTrue(obj is await obj.delete())

        self.assertEqual(True, obj.deleted)
        self.assertEqual('mid', obj.id)


if __name__ == '__main__':
    unittest.main()
