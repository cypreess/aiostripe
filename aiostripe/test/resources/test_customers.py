import datetime
import time

import aiostripe
from aiostripe.test.helper import StripeResourceTest, DUMMY_CARD, DUMMY_PLAN


class CustomerTest(StripeResourceTest):
    async def test_list_customers(self):
        await aiostripe.Customer.list()

        self.requestor_mock.request.assert_called_with('get', '/v1/customers',
                                                       {})

    async def test_create_customer(self):
        await aiostripe.Customer.create(description='foo bar', card=DUMMY_CARD, coupon='cu_discount',
                                        idempotency_key='foo')

        self.requestor_mock.request.assert_called_with('post', '/v1/customers',
                                                       {
                                                           'coupon': 'cu_discount',
                                                           'description': 'foo bar',
                                                           'card': DUMMY_CARD
                                                       },
                                                       {'Idempotency-Key': 'foo'})

    async def test_unset_description(self):
        customer = aiostripe.Customer(id='cus_unset_desc')
        customer.description = 'Hey'

        await customer.save(idempotency_key='foo')

        self.requestor_mock.request.assert_called_with('post', '/v1/customers/cus_unset_desc',
                                                       {
                                                           'description': 'Hey',
                                                       }, {'Idempotency-Key': 'foo'})

    async def test_del_coupon(self):
        customer = aiostripe.Customer(id='cus_unset_desc')
        customer.description = 'bar'
        customer.coupon = 'foo'
        del customer.coupon

        await customer.save()

        self.requestor_mock.request.assert_called_with('post', '/v1/customers/cus_unset_desc',
                                                       {
                                                           'description': 'bar'
                                                       }, None)

    def test_cannot_set_empty_string(self):
        customer = aiostripe.Customer()
        self.assertRaises(ValueError, setattr, customer, 'description', '')

    async def test_customer_add_card(self):
        customer = aiostripe.Customer.construct_from({
            'id': 'cus_add_card',
            'sources': {
                'object': 'list',
                'url': '/v1/customers/cus_add_card/sources',
            },
        }, 'api_key')

        await customer.sources.create(card=DUMMY_CARD, idempotency_key='foo')

        self.requestor_mock.request.assert_called_with('post', '/v1/customers/cus_add_card/sources',
                                                       {
                                                           'card': DUMMY_CARD,
                                                       }, {'Idempotency-Key': 'foo'})

    async def test_customer_add_source(self):
        customer = aiostripe.Customer.construct_from({
            'id': 'cus_add_source',
            'sources': {
                'object': 'list',
                'url': '/v1/customers/cus_add_source/sources',
            },
        }, 'api_key')

        await customer.sources.create(source=DUMMY_CARD, idempotency_key='foo')

        self.requestor_mock.request.assert_called_with('post', '/v1/customers/cus_add_source/sources',
                                                       {
                                                           'source': DUMMY_CARD,
                                                       }, {'Idempotency-Key': 'foo'})

    async def test_customer_update_card(self):
        card = aiostripe.Card.construct_from({
            'customer': 'cus_update_card',
            'id': 'ca_update_card',
        }, 'api_key')
        card.name = 'The Best'

        await card.save(idempotency_key='foo')

        self.requestor_mock.request.assert_called_with('post', '/v1/customers/cus_update_card/sources/ca_update_card',
                                                       {
                                                           'name': 'The Best',
                                                       }, {'Idempotency-Key': 'foo'})

    async def test_customer_update_source(self):
        source = aiostripe.BitcoinReceiver.construct_from({
            'customer': 'cus_update_source',
            'id': 'btcrcv_update_source',
        }, 'api_key')
        source.name = 'The Best'
        await source.save(idempotency_key='foo')

        self.requestor_mock.request.assert_called_with('post',
                                                       '/v1/customers/cus_update_source/sources/btcrcv_update_source',
                                                       {
                                                           'name': 'The Best',
                                                       }, {'Idempotency-Key': 'foo'})

    async def test_customer_delete_card(self):
        card = aiostripe.Card.construct_from({
            'customer': 'cus_delete_card',
            'id': 'ca_delete_card',
        }, 'api_key')

        await card.delete()

        self.requestor_mock.request.assert_called_with('delete', '/v1/customers/cus_delete_card/sources/ca_delete_card',
                                                       {}, None)

    async def test_customer_delete_source(self):
        source = aiostripe.BitcoinReceiver.construct_from({
            'customer': 'cus_delete_source',
            'id': 'btcrcv_delete_source',
        }, 'api_key')

        await source.delete()

        self.requestor_mock.request.assert_called_with('delete',
                                                       '/v1/customers/cus_delete_source/sources/btcrcv_delete_source',
                                                       {}, None)

    async def test_customer_delete_bank_account(self):
        source = aiostripe.BankAccount.construct_from({
            'customer': 'cus_delete_source',
            'id': 'ba_delete_source',
        }, 'api_key')

        await source.delete()

        self.requestor_mock.request.assert_called_with('delete',
                                                       '/v1/customers/cus_delete_source/sources/ba_delete_source',
                                                       {}, None)

    async def test_customer_verify_bank_account(self):
        source = aiostripe.BankAccount.construct_from({
            'customer': 'cus_verify_source',
            'id': 'ba_verify_source',
        }, 'api_key')

        await source.verify()

        self.requestor_mock.request.assert_called_with(
            'post',
            '/v1/customers/cus_verify_source/sources/ba_verify_source/verify',
            {}, None)


class CustomerPlanTest(StripeResourceTest):
    async def test_create_customer(self):
        await aiostripe.Customer.create(plan=DUMMY_PLAN['id'], card=DUMMY_CARD)

        self.requestor_mock.request.assert_called_with('post', '/v1/customers',
                                                       {
                                                           'card': DUMMY_CARD,
                                                           'plan': DUMMY_PLAN['id'],
                                                       }, None)

    async def test_legacy_update_subscription(self):
        customer = aiostripe.Customer(id='cus_legacy_sub_update')

        await customer.update_subscription(idempotency_key='foo', plan=DUMMY_PLAN['id'])

        self.requestor_mock.request.assert_called_with('post', '/v1/customers/cus_legacy_sub_update/subscription',
                                                       {
                                                           'plan': DUMMY_PLAN['id'],
                                                       }, {'Idempotency-Key': 'foo'})

    async def test_legacy_delete_subscription(self):
        customer = aiostripe.Customer(id='cus_legacy_sub_delete')

        await customer.cancel_subscription()

        self.requestor_mock.request.assert_called_with('delete', '/v1/customers/cus_legacy_sub_delete/subscription',
                                                       {}, None)

    async def test_create_customer_subscription(self):
        customer = aiostripe.Customer.construct_from({
            'id': 'cus_sub_create',
            'subscriptions': {
                'object': 'list',
                'url': '/v1/customers/cus_sub_create/subscriptions',
            }
        }, 'api_key')

        await customer.subscriptions.create(plan=DUMMY_PLAN['id'], coupon='foo')

        self.requestor_mock.request.assert_called_with('post', '/v1/customers/cus_sub_create/subscriptions',
                                                       {
                                                           'plan': DUMMY_PLAN['id'],
                                                           'coupon': 'foo',
                                                       }, None)

    async def test_retrieve_customer_subscription(self):
        customer = aiostripe.Customer.construct_from({
            'id': 'cus_foo',
            'subscriptions': {
                'object': 'list',
                'url': '/v1/customers/cus_foo/subscriptions',
            }
        }, 'api_key')

        await customer.subscriptions.retrieve('sub_cus')

        self.requestor_mock.request.assert_called_with('get', '/v1/customers/cus_foo/subscriptions/sub_cus',
                                                       {}, None)

    async def test_update_customer_subscription(self):
        subscription = aiostripe.Subscription.construct_from({
            'id': 'sub_update',
            'customer': 'cus_foo',
        }, 'api_key')

        trial_end_dttm = datetime.datetime.now() + datetime.timedelta(days=15)
        trial_end_int = int(time.mktime(trial_end_dttm.timetuple()))

        subscription.trial_end = trial_end_int
        subscription.plan = DUMMY_PLAN['id']

        await subscription.save()

        self.requestor_mock.request.assert_called_with('post', '/v1/customers/cus_foo/subscriptions/sub_update',
                                                       {
                                                           'plan': DUMMY_PLAN['id'],
                                                           'trial_end': trial_end_int,
                                                       }, None)

    async def test_delete_customer_subscription(self):
        subscription = aiostripe.Subscription.construct_from({
            'id': 'sub_delete',
            'customer': 'cus_foo',
        }, 'api_key')

        await subscription.delete()

        self.requestor_mock.request.assert_called_with('delete', '/v1/customers/cus_foo/subscriptions/sub_delete',
                                                       {}, None)
