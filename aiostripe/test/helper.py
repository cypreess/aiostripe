import datetime
import json
import os
import random
import string
import unittest
from unittest.mock import patch

import aiostripe
from aiostripe.resource import APIResource, SingletonAPIResource, ListableAPIResource, CreateableAPIResource, \
    UpdateableAPIResource, DeletableAPIResource
from aiostripe.test.async_helper import AsyncTestCaseMeta, AsyncMock, Mock, deasyncify

NOW = datetime.datetime.now()

DEFAULT_API_KEY = 'tGN0bIwXnHdwOa85VABjPdSn8nWY7G7I'

DUMMY_CARD = {
    'number': '4242424242424242',
    'exp_month': NOW.month,
    'exp_year': NOW.year + 4
}
DUMMY_DEBIT_CARD = {
    'number': '4000056655665556',
    'exp_month': NOW.month,
    'exp_year': NOW.year + 4
}
DUMMY_CHARGE = {
    'amount': 100,
    'currency': 'usd',
    'card': DUMMY_CARD
}

DUMMY_DISPUTE = {
    'status': 'needs_response',
    'currency': 'usd',
    'metadata': {}
}

DUMMY_PLAN = {
    'amount': 2000,
    'interval': 'month',
    'name': 'Amazing Gold Plan',
    'currency': 'usd',
    'id': ('stripe-test-gold-' +
           ''.join(random.choice(string.ascii_lowercase) for x in range(10)))
}

DUMMY_COUPON = {
    'percent_off': 25,
    'duration': 'repeating',
    'duration_in_months': 5,
    'metadata': {}
}

DUMMY_RECIPIENT = {
    'name': 'John Doe',
    'type': 'individual'
}

DUMMY_TRANSFER = {
    'amount': 400,
    'currency': 'usd',
    'recipient': 'self'
}

DUMMY_INVOICE_ITEM = {
    'amount': 456,
    'currency': 'usd',
}

SAMPLE_INVOICE = json.loads('''
{
  "amount_due": 1305,
  "attempt_count": 0,
  "attempted": true,
  "charge": "ch_wajkQ5aDTzFs5v",
  "closed": true,
  "customer": "cus_osllUe2f1BzrRT",
  "date": 1338238728,
  "discount": null,
  "ending_balance": 0,
  "id": "in_t9mHb2hpK7mml1",
  "livemode": false,
  "next_payment_attempt": null,
  "object": "invoice",
  "paid": true,
  "period_end": 1338238728,
  "period_start": 1338238716,
  "starting_balance": -8695,
  "subtotal": 10000,
  "total": 10000,
  "lines": {
    "invoiceitems": [],
    "prorations": [],
    "subscriptions": [
      {
        "plan": {
          "interval": "month",
          "object": "plan",
          "identifier": "expensive",
          "currency": "usd",
          "livemode": false,
          "amount": 10000,
          "name": "Expensive Plan",
          "trial_period_days": null,
          "id": "expensive"
        },
        "period": {
          "end": 1340917128,
          "start": 1338238728
        },
        "amount": 10000
      }
    ]
  }
}
''')


class StripeTestCase(unittest.TestCase, metaclass=AsyncTestCaseMeta):
    RESTORE_ATTRIBUTES = ('api_version', 'api_key')

    def setUp(self):
        super().setUp()

        self._stripe_original_attributes = {}

        for attr in self.RESTORE_ATTRIBUTES:
            self._stripe_original_attributes[attr] = getattr(aiostripe, attr)

        api_base = os.environ.get('STRIPE_API_BASE')
        if api_base:
            aiostripe.api_base = api_base

        aiostripe.api_key = os.environ.get('STRIPE_API_KEY', DEFAULT_API_KEY)

    def tearDown(self):
        super().tearDown()

        for attr in self.RESTORE_ATTRIBUTES:
            setattr(aiostripe, attr, self._stripe_original_attributes[attr])

    async def assertRaisesAsync(self, exception, coro, *args, **kwargs):
        with self.assertRaises(exception):
            await coro(*args, **kwargs)


class StripeUnitTestCase(StripeTestCase):
    REQUEST_LIBRARIES = ['aiohttp']

    def setUp(self):
        super().setUp()

        self.request_patchers = {}
        self.request_mocks = {}
        for lib in self.REQUEST_LIBRARIES:
            patcher = patch('aiostripe.http_client.%s' % lib)

            self.request_mocks[lib] = patcher.start()
            self.request_patchers[lib] = patcher

    def tearDown(self):
        super().tearDown()

        for patcher in self.request_patchers.values():
            patcher.stop()


class StripeApiTestCase(StripeTestCase):
    def setUp(self):
        super().setUp()

        self.requestor_patcher = patch('aiostripe.api_requestor.APIRequestor')
        requestor_class_mock = self.requestor_patcher.start()
        self.requestor_mock = requestor_class_mock.return_value

    def tearDown(self):
        super().tearDown()

        self.requestor_patcher.stop()

    def mock_response(self, res):
        self.requestor_mock.request = Mock(return_value=(res, 'reskey'))


class StripeResourceTest(StripeApiTestCase):
    def setUp(self):
        super().setUp()
        self.mock_response({})


class MyResource(APIResource):
    pass


class MySingleton(SingletonAPIResource):
    pass


class MyListable(ListableAPIResource):
    pass


class MyCreatable(CreateableAPIResource):
    pass


class MyUpdateable(UpdateableAPIResource):
    pass


class MyDeletable(DeletableAPIResource):
    pass


class MyComposite(ListableAPIResource, CreateableAPIResource, UpdateableAPIResource, DeletableAPIResource):
    pass


__all__ = ['Mock', 'AsyncMock', 'AsyncTestCaseMeta', 'deasyncify',
           'DEFAULT_API_KEY', 'NOW',
           'DUMMY_CARD', 'DUMMY_CHARGE', 'DUMMY_COUPON', 'DUMMY_DEBIT_CARD', 'DUMMY_DISPUTE', 'DUMMY_INVOICE_ITEM',
           'DUMMY_PLAN', 'DUMMY_RECIPIENT', 'DUMMY_TRANSFER',
           'SAMPLE_INVOICE',
           'MyComposite', 'MyCreatable', 'MyDeletable', 'MyListable', 'MyResource', 'MySingleton', 'MyUpdateable',
           'StripeApiTestCase', 'StripeResourceTest', 'StripeTestCase', 'StripeUnitTestCase']
