# -*- coding: utf-8 -*-

import unittest2

from stripe import StripeError
from stripe.test.helper import StripeUnitTestCase


class StripeErrorTests(StripeUnitTestCase):
    def test_formatting(self):
        err = StripeError('öre')
        assert str(err) == 'öre'

    def test_formatting_with_request_id(self):
        err = StripeError('öre', headers={'request-id': '123'})
        assert str(err) == 'Request 123: öre'


if __name__ == '__main__':
    unittest2.main()
