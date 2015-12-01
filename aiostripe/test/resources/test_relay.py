import aiostripe
from aiostripe.test.helper import StripeResourceTest


class ProductTest(StripeResourceTest):
    async def test_list_products(self):
        await aiostripe.Product.list()

        self.requestor_mock.request.assert_called_with('get', '/v1/products', {})


class SKUTest(StripeResourceTest):
    async def test_list_skus(self):
        await aiostripe.SKU.list()

        self.requestor_mock.request.assert_called_with('get', '/v1/skus', {})


class OrderTest(StripeResourceTest):
    async def test_list_orders(self):
        await aiostripe.Order.list()

        self.requestor_mock.request.assert_called_with('get', '/v1/orders', {})

    async def test_pay_order(self):
        order = aiostripe.Order(id='or_pay')

        await order.pay()

        self.requestor_mock.request.assert_called_with('post', '/v1/orders/or_pay/pay', {}, None)
