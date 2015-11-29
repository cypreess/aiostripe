import stripe
from stripe.test.helper import (
    StripeResourceTest, NOW, DUMMY_CHARGE
)


class ChargeTest(StripeResourceTest):
    async def test_charge_list_all(self):
        await stripe.Charge.list(created={'lt': NOW})

        self.requestor_mock.request.assert_called_with(
            'get',
            '/v1/charges',
            {
                'created': {'lt': NOW},
            }
        )

    async def test_charge_list_create(self):
        await stripe.Charge.create(idempotency_key='foo', **DUMMY_CHARGE)

        self.requestor_mock.request.assert_called_with(
            'post',
            '/v1/charges',
            DUMMY_CHARGE,
            {'Idempotency-Key': 'foo'},
        )

    async def test_charge_list_retrieve(self):
        await stripe.Charge.retrieve('ch_test_id')

        self.requestor_mock.request.assert_called_with(
            'get',
            '/v1/charges/ch_test_id',
            {},
            None
        )

    async def test_charge_update_dispute(self):
        charge = stripe.Charge(id='ch_update_id')
        await charge.update_dispute(idempotency_key='foo')

        self.requestor_mock.request.assert_called_with(
            'post',
            '/v1/charges/ch_update_id/dispute',
            {},
            {'Idempotency-Key': 'foo'},
        )

    async def test_charge_close_dispute(self):
        charge = stripe.Charge(id='ch_update_id')
        await charge.close_dispute(idempotency_key='foo')

        self.requestor_mock.request.assert_called_with(
            'post',
            '/v1/charges/ch_update_id/dispute/close',
            {},
            {'Idempotency-Key': 'foo'},
        )

    async def test_mark_as_fraudulent(self):
        charge = stripe.Charge(id='ch_update_id')
        await charge.mark_as_fraudulent(idempotency_key='foo')

        self.requestor_mock.request.assert_called_with(
            'post',
            '/v1/charges/ch_update_id',
            {
                'fraud_details': {'user_report': 'fraudulent'}
            },
            {'Idempotency-Key': 'foo'},
        )

    async def test_mark_as_safe(self):
        charge = stripe.Charge(id='ch_update_id')
        await charge.mark_as_safe(idempotency_key='foo')

        self.requestor_mock.request.assert_called_with(
            'post',
            '/v1/charges/ch_update_id',
            {
                'fraud_details': {'user_report': 'safe'}
            },
            {'Idempotency-Key': 'foo'},
        )

    async def test_create_with_source_param(self):
        await stripe.Charge.create(amount=100, currency='usd',
                             source='btcrcv_test_receiver')

        self.requestor_mock.request.assert_called_with(
            'post',
            '/v1/charges',
            {
                'amount': 100,
                'currency': 'usd',
                'source': 'btcrcv_test_receiver'
            },
            None,
        )
