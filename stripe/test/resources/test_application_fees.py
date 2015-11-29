import stripe
from stripe.test.helper import StripeResourceTest


class ApplicationFeeTest(StripeResourceTest):
    async def test_list_application_fees(self):
        await stripe.ApplicationFee.list()
        self.requestor_mock.request.assert_called_with(
            'get',
            '/v1/application_fees',
            {}
        )


class ApplicationFeeRefundTest(StripeResourceTest):
    @desync
    async def test_fetch_refund(self):
        fee = stripe.ApplicationFee.construct_from({
            'id': 'fee_get_refund',
            'refunds': {
                'object': 'list',
                'url': '/v1/application_fees/fee_get_refund/refunds',
            }
        }, 'api_key')

        await fee.refunds.retrieve("ref_get")

        self.requestor_mock.request.assert_called_with(
            'get',
            '/v1/application_fees/fee_get_refund/refunds/ref_get',
            {},
            None
        )

    @desync
    async def test_list_refunds(self):
        fee = stripe.ApplicationFee.construct_from({
            'id': 'fee_get_refund',
            'refunds': {
                'object': 'list',
                'url': '/v1/application_fees/fee_get_refund/refunds',
            }
        }, 'api_key')

        await fee.refunds.list()

        self.requestor_mock.request.assert_called_with(
            'get',
            '/v1/application_fees/fee_get_refund/refunds',
            {},
            None
        )

    async def test_update_refund(self):
        refund = stripe.resource.ApplicationFeeRefund.construct_from({
            'id': "ref_update",
            'fee': "fee_update",
            'metadata': {},
        }, 'api_key')
        refund.metadata["key"] = "value"
        await refund.save()

        self.requestor_mock.request.assert_called_with(
            'post',
            '/v1/application_fees/fee_update/refunds/ref_update',
            {
                'metadata': {
                    'key': 'value',
                }
            },
            None
        )
