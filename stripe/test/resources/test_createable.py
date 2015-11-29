import stripe
from stripe.test.helper import (
    StripeApiTestCase, MyCreatable
)


class CreateableAPIResourceTests(StripeApiTestCase):
    async def test_create(self):
        self.mock_response({
            'object': 'charge',
            'foo': 'bar',
        })

        res = await MyCreatable.create()

        self.requestor_mock.request.assert_called_with(
            'post', '/v1/mycreatables', {}, None)

        self.assertTrue(isinstance(res, stripe.Charge))
        self.assertEqual('bar', res.foo)

    async def test_idempotent_create(self):
        self.mock_response({
            'object': 'charge',
            'foo': 'bar',
        })

        res = await MyCreatable.create(idempotency_key='foo')

        self.requestor_mock.request.assert_called_with(
            'post', '/v1/mycreatables', {}, {'Idempotency-Key': 'foo'})

        self.assertTrue(isinstance(res, stripe.Charge))
        self.assertEqual('bar', res.foo)
