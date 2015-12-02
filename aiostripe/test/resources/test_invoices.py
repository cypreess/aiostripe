import unittest

import aiostripe
from aiostripe.test.helper import StripeResourceTest, DUMMY_INVOICE_ITEM


class InvoiceTest(StripeResourceTest):
    async def test_add_invoice_item(self):
        customer = aiostripe.Customer(id='cus_invoice_items')

        await customer.add_invoice_item(**DUMMY_INVOICE_ITEM)

        expected = DUMMY_INVOICE_ITEM.copy()
        expected['customer'] = 'cus_invoice_items'

        self.requestor_mock.request.assert_called_with('post', '/v1/invoiceitems',
                                                       expected, None)

    async def test_retrieve_invoice_items(self):
        customer = aiostripe.Customer(id='cus_get_invoice_items')

        await customer.invoice_items()

        self.requestor_mock.request.assert_called_with('get', '/v1/invoiceitems',
                                                       {'customer': 'cus_get_invoice_items'})

    async def test_invoice_create(self):
        customer = aiostripe.Customer(id='cus_invoice')

        await aiostripe.Invoice.create(customer=customer.id)

        self.requestor_mock.request.assert_called_with('post', '/v1/invoices',
                                                       {
                                                           'customer': 'cus_invoice',
                                                       }, None)

    async def test_retrieve_customer_invoices(self):
        customer = aiostripe.Customer(id='cus_invoice_items')

        await customer.invoices()

        self.requestor_mock.request.assert_called_with('get', '/v1/invoices',
                                                       {
                                                           'customer': 'cus_invoice_items',
                                                       })

    async def test_pay_invoice(self):
        invoice = aiostripe.Invoice(id='ii_pay')

        await invoice.pay()

        self.requestor_mock.request.assert_called_with('post', '/v1/invoices/ii_pay/pay',
                                                       {}, None)

    async def test_upcoming_invoice(self):
        await aiostripe.Invoice.upcoming()

        self.requestor_mock.request.assert_called_with('get', '/v1/invoices/upcoming',
                                                       {})


if __name__ == '__main__':
    unittest.main()
