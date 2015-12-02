import unittest

import aiostripe
from aiostripe.test.helper import StripeResourceTest, DUMMY_COUPON


class CouponTest(StripeResourceTest):
    async def test_create_coupon(self):
        await aiostripe.Coupon.create(**DUMMY_COUPON)

        self.requestor_mock.request.assert_called_with('post', '/v1/coupons',
                                                       DUMMY_COUPON, None)

    async def test_update_coupon(self):
        coup = aiostripe.Coupon.construct_from({
            'id': 'cu_update',
            'metadata': {},
        }, 'api_key')
        coup.metadata['key'] = 'value'

        await coup.save()

        self.requestor_mock.request.assert_called_with('post', '/v1/coupons/cu_update',
                                                       {
                                                           'metadata': {
                                                               'key': 'value',
                                                           }
                                                       }, None)

    async def test_delete_coupon(self):
        c = aiostripe.Coupon(id='cu_delete')

        await c.delete()

        self.requestor_mock.request.assert_called_with('delete', '/v1/coupons/cu_delete',
                                                       {}, None)

    async def test_detach_coupon(self):
        customer = aiostripe.Customer(id='cus_delete_discount')

        await customer.delete_discount()

        self.requestor_mock.request.assert_called_with('delete', '/v1/customers/cus_delete_discount/discount')


if __name__ == '__main__':
    unittest.main()
