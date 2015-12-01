# coding: utf8
import unittest
from unittest.mock import patch

import aiostripe
import aiostripe.error
import aiostripe.http_client
from aiostripe.test.helper import StripeTestCase, NOW, DUMMY_CHARGE, DUMMY_CARD


class FunctionalTests(StripeTestCase):
    request_client = aiostripe.http_client.AsyncioClient

    def setUp(self):
        super().setUp()

        def get_http_client(*args, **kwargs):
            return self.request_client(*args, **kwargs)

        self.client_patcher = patch('aiostripe.http_client.new_default_http_client')

        client_mock = self.client_patcher.start()
        client_mock.side_effect = get_http_client

    def tearDown(self):
        super().tearDown()

        self.client_patcher.stop()

    async def test_dns_failure(self):
        api_base = aiostripe.api_base
        try:
            aiostripe.api_base = 'https://my-invalid-domain.ireallywontresolve/v1'

            await self.assertRaisesAsync(aiostripe.error.APIConnectionError, aiostripe.Customer.create)
        finally:
            aiostripe.api_base = api_base

    async def test_run(self):
        charge = await aiostripe.Charge.create(**DUMMY_CHARGE)
        self.assertFalse(charge.refunded)
        await charge.refund()
        self.assertTrue(charge.refunded)

    async def test_refresh(self):
        charge = await aiostripe.Charge.create(**DUMMY_CHARGE)
        charge2 = await aiostripe.Charge.retrieve(charge.id)
        self.assertEqual(charge2.created, charge.created)

        charge2.junk = 'junk'
        await charge2.refresh()
        self.assertRaises(AttributeError, lambda: charge2.junk)

    async def test_list_accessors(self):
        customer = await aiostripe.Customer.create(card=DUMMY_CARD)
        self.assertEqual(customer['created'], customer.created)
        customer['foo'] = 'bar'
        self.assertEqual(customer.foo, 'bar')

    async def test_raise(self):
        EXPIRED_CARD = DUMMY_CARD.copy()
        EXPIRED_CARD['exp_month'] = NOW.month - 2
        EXPIRED_CARD['exp_year'] = NOW.year - 2
        await self.assertRaisesAsync(aiostripe.error.CardError, aiostripe.Charge.create, amount=100, currency='usd',
                                     card=EXPIRED_CARD)

    async def test_response_headers(self):
        EXPIRED_CARD = DUMMY_CARD.copy()
        EXPIRED_CARD['exp_month'] = NOW.month - 2
        EXPIRED_CARD['exp_year'] = NOW.year - 2
        try:
            await aiostripe.Charge.create(amount=100, currency='usd', card=EXPIRED_CARD)
            self.fail('charge creation with expired card did not fail')
        except aiostripe.error.CardError as e:
            self.assertTrue(e.request_id.startswith('req_'))

    async def test_unicode(self):
        # Make sure unicode requests can be sent
        await self.assertRaisesAsync(aiostripe.error.InvalidRequestError, aiostripe.Charge.retrieve, id='☃')

    async def test_none_values(self):
        customer = await aiostripe.Customer.create(plan=None)
        self.assertTrue(customer.id)

    async def test_missing_id(self):
        customer = aiostripe.Customer()
        await self.assertRaisesAsync(aiostripe.error.InvalidRequestError, customer.refresh)


class AuthenticationErrorTest(StripeTestCase):
    async def test_invalid_credentials(self):
        key = aiostripe.api_key
        try:
            aiostripe.api_key = 'invalid'
            await aiostripe.Customer.create()
        except aiostripe.error.AuthenticationError as e:
            self.assertEqual(401, e.http_status)
            self.assertTrue(isinstance(e.http_body, str))
            self.assertTrue(isinstance(e.json_body, dict))
            self.assertTrue(e.request_id.startswith('req_'))
        finally:
            aiostripe.api_key = key


class CardErrorTest(StripeTestCase):
    async def test_declined_card_props(self):
        EXPIRED_CARD = DUMMY_CARD.copy()
        EXPIRED_CARD['exp_month'] = NOW.month - 2
        EXPIRED_CARD['exp_year'] = NOW.year - 2
        try:
            await aiostripe.Charge.create(amount=100, currency='usd', card=EXPIRED_CARD)
        except aiostripe.error.CardError as e:
            self.assertEqual(402, e.http_status)
            self.assertTrue(isinstance(e.http_body, str))
            self.assertTrue(isinstance(e.json_body, dict))
            self.assertTrue(e.request_id.startswith('req_'))


class InvalidRequestErrorTest(StripeTestCase):
    async def test_nonexistent_object(self):
        try:
            await aiostripe.Charge.retrieve('invalid')
        except aiostripe.error.InvalidRequestError as e:
            self.assertEqual(404, e.http_status)
            self.assertTrue(isinstance(e.http_body, str))
            self.assertTrue(isinstance(e.json_body, dict))
            self.assertTrue(e.request_id.startswith('req_'))

    async def test_invalid_data(self):
        try:
            await aiostripe.Charge.create()
        except aiostripe.error.InvalidRequestError as e:
            self.assertEqual(400, e.http_status)
            self.assertTrue(isinstance(e.http_body, str))
            self.assertTrue(isinstance(e.json_body, dict))
            self.assertTrue(e.request_id.startswith('req_'))


if __name__ == '__main__':
    unittest.main()
