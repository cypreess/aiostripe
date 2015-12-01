import json
from urllib.parse import quote_plus

from aiostripe import api_requestor, error, upload_api_base
from aiostripe.logger import logger


def convert_to_stripe_object(resp, api_key, account):
    types = {
        'account': Account,
        'application_fee': ApplicationFee,
        'bank_account': BankAccount,
        'bitcoin_receiver': BitcoinReceiver,
        'bitcoin_transaction': BitcoinTransaction,
        'card': Card,
        'charge': Charge,
        'coupon': Coupon,
        'customer': Customer,
        'dispute': Dispute,
        'event': Event,
        'fee_refund': ApplicationFeeRefund,
        'file_upload': FileUpload,
        'invoice': Invoice,
        'invoiceitem': InvoiceItem,
        'list': ListObject,
        'plan': Plan,
        'recipient': Recipient,
        'refund': Refund,
        'subscription': Subscription,
        'token': Token,
        'transfer': Transfer,
        'transfer_reversal': Reversal,
        'product': Product,
        'sku': SKU,
        'order': Order
    }

    if isinstance(resp, list):
        return [convert_to_stripe_object(i, api_key, account) for i in resp]

    elif isinstance(resp, dict) and not isinstance(resp, StripeObject):
        resp = resp.copy()
        klass_name = resp.get('object')

        if isinstance(klass_name, str):
            klass = types.get(klass_name, StripeObject)
        else:
            klass = StripeObject

        return klass.construct_from(resp, api_key, stripe_account=account)
    else:
        return resp


def populate_headers(idempotency_key):
    if idempotency_key is not None:
        return {'Idempotency-Key': idempotency_key}

    return None


def _compute_diff(current, previous):
    if isinstance(current, dict):
        previous = previous or {}
        diff = current.copy()

        for key in set(previous.keys()) - set(diff.keys()):
            diff[key] = ''

        return diff

    return current if current is not None else ''


def _serialize_list(array, previous):
    array = array or []
    previous = previous or []
    params = {}

    for i, v in enumerate(array):
        previous_item = previous[i] if len(previous) > i else None

        if hasattr(v, 'serialize'):
            params[str(i)] = v.serialize(previous_item)
        else:
            params[str(i)] = _compute_diff(v, previous_item)

    return params


class StripeObject(dict):
    def __init__(self, id=None, api_key=None, stripe_account=None, **kwargs):
        super().__init__()

        self._unsaved_values = set()
        self._transient_values = set()

        self._retrieve_params = kwargs
        self._previous = None

        super().__setattr__('api_key', api_key)
        super().__setattr__('stripe_account', stripe_account)

        if id:
            self['id'] = id

    def update(self, update_dict=None, **kwargs):
        if update_dict is not None:
            for k in update_dict:
                self._unsaved_values.add(k)

        for k in kwargs:
            self._unsaved_values.add(k)

        return super().update(update_dict, **kwargs)

    def __setattr__(self, k, v):
        if k[0] == '_' or k in self.__dict__:
            return super().__setattr__(k, v)
        else:
            self[k] = v

    def __getattr__(self, k):
        if k[0] == '_':
            raise AttributeError(k)

        try:
            return self[k]
        except KeyError as err:
            raise AttributeError(*err.args) from err

    def __delattr__(self, k):
        if k[0] == '_' or k in self.__dict__:
            return super().__delattr__(k)
        else:
            del self[k]

    def __setitem__(self, k, v):
        if v == '':
            raise ValueError('You cannot set %s to an empty string. We interpret empty strings as None in requests. '
                             'You may set %s.%s = None to delete the property' % (k, self, k))

        super().__setitem__(k, v)

        # Allows for unpickling in Python 3.x
        if not hasattr(self, '_unsaved_values'):
            self._unsaved_values = set()

        self._unsaved_values.add(k)

    def __getitem__(self, k):
        try:
            return super().__getitem__(k)
        except KeyError as err:
            if k in self._transient_values:
                raise KeyError('%r.  HINT: The %r attribute was set in the past. It was then wiped when refreshing the '
                               'object with the result returned by Stripe\'s API, probably as a result of a save().  '
                               'The attributes currently available on this object are: %s' %
                               (k, k, ', '.join(list(self.keys())))) from err
            else:
                raise

    def __delitem__(self, k):
        super().__delitem__(k)

        # Allows for unpickling in Python 3.x
        if hasattr(self, '_unsaved_values'):
            self._unsaved_values.remove(k)

    @classmethod
    def construct_from(cls, values, key, stripe_account=None):
        instance = cls(values.get('id'), api_key=key, stripe_account=stripe_account)
        instance.refresh_from(values, api_key=key, stripe_account=stripe_account)
        return instance

    def refresh_from(self, values, api_key=None, partial=False, stripe_account=None):
        self.api_key = api_key or getattr(values, 'api_key', None)
        self.stripe_account = stripe_account or getattr(values, 'stripe_account', None)

        # Wipe old state before setting new.  This is useful for e.g.
        # updating a customer, where there is no persistent card
        # parameter.  Mark those values which don't persist as transient
        if partial:
            self._unsaved_values = (self._unsaved_values - set(values))
        else:
            removed = set(self.keys()) - set(values)
            self._transient_values = self._transient_values | removed
            self._unsaved_values = set()
            self.clear()

        self._transient_values = self._transient_values - set(values)

        for k, v in values.items():
            super().__setitem__(k, convert_to_stripe_object(v, api_key, stripe_account))

        self._previous = values

    @classmethod
    def api_base(cls):
        return None

    async def request(self, method, url, params=None, headers=None):
        if params is None:
            params = self._retrieve_params

        requestor = api_requestor.APIRequestor(key=self.api_key, api_base=self.api_base(), account=self.stripe_account)
        response, api_key = await requestor.request(method, url, params, headers)

        return convert_to_stripe_object(response, api_key, self.stripe_account)

    def __repr__(self):
        ident_parts = [type(self).__name__]

        if isinstance(self.get('object'), str):
            ident_parts.append(self.get('object'))

        if isinstance(self.get('id'), str):
            ident_parts.append('id=%s' % self.get('id'))

        unicode_repr = '<%s at %s> JSON: %s' % (' '.join(ident_parts), hex(id(self)), self)

        return unicode_repr

    def __str__(self):
        return json.dumps(self, sort_keys=True, indent=2)

    @property
    def stripe_id(self):
        return self.id

    def serialize(self, previous):
        params = {}
        unsaved_keys = self._unsaved_values or set()
        previous = previous or self._previous or {}

        for k, v in list(self.items()):
            if k == 'id' or (isinstance(k, str) and k.startswith('_')):
                continue
            elif isinstance(v, APIResource):
                continue
            elif hasattr(v, 'serialize'):
                params[k] = v.serialize(previous.get(k, None))
            elif k in unsaved_keys:
                params[k] = _compute_diff(v, previous.get(k, None))
            elif k == 'additional_owners' and v is not None:
                params[k] = _serialize_list(v, previous.get(k, []))

        return params


class APIResource(StripeObject):
    @classmethod
    async def retrieve(cls, id, api_key=None, **kwargs):
        instance = cls(id, api_key, **kwargs)

        await instance.refresh()

        return instance

    async def refresh(self):
        self.refresh_from(await self.request('get', self.instance_url()))

        return self

    @classmethod
    def class_name(cls):
        if cls is APIResource:
            raise NotImplementedError('APIResource is an abstract class.  You should perform actions on its subclasses '
                                      '(e.g. Charge, Customer)')

        return str(quote_plus(cls.__name__.lower()))

    @classmethod
    def class_url(cls):
        cls_name = cls.class_name()

        return '/v1/%ss' % cls_name

    def instance_url(self):
        id = self.get('id')

        if not id:
            raise error.InvalidRequestError('Could not determine which URL to request: %s instance has invalid ID: %r' %
                                            (type(self).__name__, id), 'id')

        base = self.class_url()
        extn = quote_plus(id)

        return '%s/%s' % (base, extn)


class ListObject(StripeObject):
    async def list(self, **kwargs):
        return await self.request('get', self['url'], kwargs)

    def auto_paging_iter(self):
        page = self
        params = dict(self._retrieve_params)

        while True:
            item_id = None
            for item in page:
                item_id = item.get('id', None)
                yield item

            if not getattr(page, 'has_more', False) or item_id is None:
                return

            params['starting_after'] = item_id
            page = self.list(**params)

    async def create(self, idempotency_key=None, **kwargs):
        headers = populate_headers(idempotency_key)

        return await self.request('post', self['url'], kwargs, headers)

    async def retrieve(self, id, **kwargs):
        base = self.get('url')
        extn = quote_plus(id)
        url = '%s/%s' % (base, extn)

        return await self.request('get', url, kwargs)

    def __iter__(self):
        return iter(getattr(self, 'data', []))


class SingletonAPIResource(APIResource):
    @classmethod
    async def retrieve(cls, **kwargs):
        return await super().retrieve(None, **kwargs)

    @classmethod
    def class_url(cls):
        cls_name = cls.class_name()

        return '/v1/%s' % cls_name

    def instance_url(self):
        return self.class_url()


# Classes of API operations
class ListableAPIResource(APIResource):
    @classmethod
    async def auto_paging_iter(cls, *args, **kwargs):
        return (await cls.list(*args, **kwargs)).auto_paging_iter()

    @classmethod
    async def list(cls, api_key=None, idempotency_key=None, stripe_account=None, **kwargs):
        requestor = api_requestor.APIRequestor(api_key, account=stripe_account)
        url = cls.class_url()

        response, api_key = await requestor.request('get', url, kwargs)

        return convert_to_stripe_object(response, api_key, stripe_account)


class CreateableAPIResource(APIResource):
    @classmethod
    async def create(cls, api_key=None, idempotency_key=None, stripe_account=None, **kwargs):
        requestor = api_requestor.APIRequestor(api_key, account=stripe_account)
        url = cls.class_url()
        headers = populate_headers(idempotency_key)

        response, api_key = await requestor.request('post', url, kwargs, headers)

        return convert_to_stripe_object(response, api_key, stripe_account)


class UpdateableAPIResource(APIResource):
    async def save(self, idempotency_key=None):
        updated_params = self.serialize(None)
        headers = populate_headers(idempotency_key)

        if updated_params:
            self.refresh_from(await self.request('post', self.instance_url(), updated_params, headers))
        else:
            logger.debug('Trying to save already saved object %r', self)

        return self


class DeletableAPIResource(APIResource):
    async def delete(self, **kwargs):
        self.refresh_from(await self.request('delete', self.instance_url(), kwargs))

        return self


# API objects
class Account(CreateableAPIResource, ListableAPIResource, UpdateableAPIResource, DeletableAPIResource):
    @classmethod
    def retrieve(cls, id=None, api_key=None, **kwargs):
        instance = cls(id, api_key, **kwargs)
        instance.refresh()

        return instance

    def instance_url(self):
        id = self.get('id')
        if not id:
            return '/v1/account'

        base = self.class_url()
        extn = quote_plus(id)

        return '%s/%s' % (base, extn)


class Balance(SingletonAPIResource):
    pass


class BalanceTransaction(ListableAPIResource):
    @classmethod
    def class_url(cls):
        return '/v1/balance/history'


class Card(UpdateableAPIResource, DeletableAPIResource):
    def instance_url(self):
        extn = quote_plus(self.id)

        if hasattr(self, 'customer'):
            customer = self.customer

            base = Customer.class_url()
            owner_extn = quote_plus(customer)
            class_base = 'sources'

        elif hasattr(self, 'recipient'):
            recipient = self.recipient

            base = Recipient.class_url()
            owner_extn = quote_plus(recipient)
            class_base = 'cards'

        elif hasattr(self, 'account'):
            account = self.account

            base = Account.class_url()
            owner_extn = quote_plus(account)
            class_base = 'external_accounts'

        else:
            raise error.InvalidRequestError('Could not determine whether card_id %s is attached to a customer, '
                                            'recipient, or account.' % self.id, 'id')

        return '%s/%s/%s/%s' % (base, owner_extn, class_base, extn)

    @classmethod
    def retrieve(cls, id, api_key=None, stripe_account=None, **kwargs):
        raise NotImplementedError("Can't retrieve a card without a customer, recipient or account ID. Use "
                                  "customer.sources.retrieve('card_id'), recipient.cards.retrieve('card_id'), or "
                                  "account.external_accounts.retrieve('card_id') instead.")


class VerifyMixin(object):
    async def verify(self, idempotency_key=None, **kwargs):
        url = self.instance_url() + '/verify'
        headers = populate_headers(idempotency_key)
        self.refresh_from(await self.request('post', url, kwargs, headers))

        return self


class BankAccount(UpdateableAPIResource, DeletableAPIResource, VerifyMixin):
    def instance_url(self):
        extn = quote_plus(self.id)
        if hasattr(self, 'customer'):
            customer = self.customer

            base = Customer.class_url()
            owner_extn = quote_plus(customer)
            class_base = 'sources'

        elif hasattr(self, 'account'):
            account = self.account

            base = Account.class_url()
            owner_extn = quote_plus(account)
            class_base = 'external_accounts'

        else:
            raise error.InvalidRequestError('Could not determine whether bank_account_id %s is attached to a customer '
                                            'or an account.' % self.id, 'id')

        return '%s/%s/%s/%s' % (base, owner_extn, class_base, extn)

    @classmethod
    def retrieve(cls, id, api_key=None, stripe_account=None, **kwargs):
        raise NotImplementedError("Can't retrieve a bank account without a customer or account ID. Use "
                                  "customer.sources.retrieve('bank_account_id') or "
                                  "account.external_accounts.retrieve('bank_account_id') instead.")


class Charge(CreateableAPIResource, ListableAPIResource, UpdateableAPIResource):
    async def refund(self, idempotency_key=None, **kwargs):
        url = self.instance_url() + '/refund'
        headers = populate_headers(idempotency_key)
        self.refresh_from(await self.request('post', url, kwargs, headers))

        return self

    async def capture(self, idempotency_key=None, **kwargs):
        url = self.instance_url() + '/capture'
        headers = populate_headers(idempotency_key)
        self.refresh_from(await self.request('post', url, kwargs, headers))

        return self

    async def update_dispute(self, idempotency_key=None, **kwargs):
        requestor = api_requestor.APIRequestor(self.api_key, account=self.stripe_account)
        url = self.instance_url() + '/dispute'
        headers = populate_headers(idempotency_key)
        response, api_key = await requestor.request('post', url, kwargs, headers)
        self.refresh_from({'dispute': response}, api_key, True)

        return self.dispute

    async def close_dispute(self, idempotency_key=None):
        requestor = api_requestor.APIRequestor(self.api_key, account=self.stripe_account)
        url = self.instance_url() + '/dispute/close'
        headers = populate_headers(idempotency_key)
        response, api_key = await requestor.request('post', url, {}, headers)
        self.refresh_from({'dispute': response}, api_key, True)

        return self.dispute

    async def mark_as_fraudulent(self, idempotency_key=None):
        url = self.instance_url()
        params = {'fraud_details': {'user_report': 'fraudulent'}}
        headers = populate_headers(idempotency_key)
        self.refresh_from(await self.request('post', url, params, headers))

        return self

    async def mark_as_safe(self, idempotency_key=None):
        url = self.instance_url()
        params = {'fraud_details': {'user_report': 'safe'}}
        headers = populate_headers(idempotency_key)
        self.refresh_from(await self.request('post', url, params, headers))

        return self


class Dispute(CreateableAPIResource, ListableAPIResource, UpdateableAPIResource):
    async def close(self, idempotency_key=None):
        url = self.instance_url() + '/close'
        headers = populate_headers(idempotency_key)
        self.refresh_from(await self.request('post', url, {}, headers))

        return self


class Customer(CreateableAPIResource, UpdateableAPIResource, ListableAPIResource, DeletableAPIResource):
    async def add_invoice_item(self, idempotency_key=None, **kwargs):
        kwargs['customer'] = self.id
        ii = await InvoiceItem.create(self.api_key, idempotency_key=idempotency_key, **kwargs)

        return ii

    async def invoices(self, **kwargs):
        kwargs['customer'] = self.id
        invoices = await Invoice.list(self.api_key, **kwargs)

        return invoices

    async def invoice_items(self, **kwargs):
        kwargs['customer'] = self.id
        iis = await InvoiceItem.list(self.api_key, **kwargs)

        return iis

    async def charges(self, **kwargs):
        kwargs['customer'] = self.id
        charges = await Charge.list(self.api_key, **kwargs)

        return charges

    async def delete_discount(self, **kwargs):
        requestor = api_requestor.APIRequestor(self.api_key, account=self.stripe_account)
        url = self.instance_url() + '/discount'

        _, api_key = await requestor.request('delete', url)

        self.refresh_from({'discount': None}, api_key, True)


class Invoice(CreateableAPIResource, ListableAPIResource, UpdateableAPIResource):
    async def pay(self, idempotency_key=None):
        headers = populate_headers(idempotency_key)
        return await self.request('post', self.instance_url() + '/pay', {}, headers)

    @classmethod
    async def upcoming(cls, api_key=None, stripe_account=None, **kwargs):
        requestor = api_requestor.APIRequestor(api_key, account=stripe_account)
        url = cls.class_url() + '/upcoming'
        response, api_key = await requestor.request('get', url, kwargs)

        return convert_to_stripe_object(response, api_key, stripe_account)


class InvoiceItem(CreateableAPIResource, UpdateableAPIResource, ListableAPIResource, DeletableAPIResource):
    pass


class Plan(CreateableAPIResource, DeletableAPIResource, UpdateableAPIResource, ListableAPIResource):
    pass


class Subscription(UpdateableAPIResource, DeletableAPIResource):
    def instance_url(self):
        base = Customer.class_url()
        cust_extn = quote_plus(self.customer)
        extn = quote_plus(self.id)

        return '%s/%s/subscriptions/%s' % (base, cust_extn, extn)

    @classmethod
    async def retrieve(cls, id, api_key=None, **kwargs):
        raise NotImplementedError("Can't retrieve a subscription without a customer ID. Use "
                                  "customer.subscriptions.retrieve('subscription_id') instead.")

    async def delete_discount(self, **kwargs):
        requestor = api_requestor.APIRequestor(self.api_key,
                                               account=self.stripe_account)
        url = self.instance_url() + '/discount'

        _, api_key = await requestor.request('delete', url)

        self.refresh_from({'discount': None}, api_key, True)


class Refund(CreateableAPIResource, ListableAPIResource, UpdateableAPIResource):
    pass


class Token(CreateableAPIResource):
    pass


class Coupon(CreateableAPIResource, UpdateableAPIResource, DeletableAPIResource, ListableAPIResource):
    pass


class Event(ListableAPIResource):
    pass


class Transfer(CreateableAPIResource, UpdateableAPIResource, ListableAPIResource):
    async def cancel(self):
        self.refresh_from(await self.request('post', self.instance_url() + '/cancel'))


class Reversal(UpdateableAPIResource):
    def instance_url(self):
        base = Transfer.class_url()
        cust_extn = quote_plus(self.transfer)
        extn = quote_plus(self.id)

        return '%s/%s/reversals/%s' % (base, cust_extn, extn)

    @classmethod
    async def retrieve(cls, id, api_key=None, **kwargs):
        raise NotImplementedError("Can't retrieve a reversal without a transfer ID. Use "
                                  "transfer.reversals.retrieve('reversal_id')")


class Recipient(CreateableAPIResource, UpdateableAPIResource, ListableAPIResource, DeletableAPIResource):
    async def transfers(self, **kwargs):
        kwargs['recipient'] = self.id
        transfers = await Transfer.list(self.api_key, **kwargs)

        return transfers


class FileUpload(ListableAPIResource):
    @classmethod
    def api_base(cls):
        return upload_api_base

    @classmethod
    def class_name(cls):
        return 'file'

    @classmethod
    async def create(cls, api_key=None, stripe_account=None, **kwargs):
        requestor = api_requestor.APIRequestor(api_key, api_base=cls.api_base(), account=stripe_account)
        url = cls.class_url()
        supplied_headers = {
            'Content-Type': 'multipart/form-data'
        }
        response, api_key = await requestor.request('post', url, params=kwargs, headers=supplied_headers)
        return convert_to_stripe_object(response, api_key, stripe_account)


class ApplicationFee(ListableAPIResource):
    @classmethod
    def class_name(cls):
        return 'application_fee'

    async def refund(self, idempotency_key=None, **kwargs):
        headers = populate_headers(idempotency_key)
        url = self.instance_url() + '/refund'
        self.refresh_from(await self.request('post', url, kwargs, headers))

        return self


class ApplicationFeeRefund(UpdateableAPIResource):
    def instance_url(self):
        base = ApplicationFee.class_url()
        cust_extn = quote_plus(self.fee)
        extn = quote_plus(self.id)

        return '%s/%s/refunds/%s' % (base, cust_extn, extn)

    @classmethod
    async def retrieve(cls, id, api_key=None, **kwargs):
        raise NotImplementedError("Can't retrieve a refund without an application fee ID. Use "
                                  "application_fee.refunds.retrieve('refund_id') instead.")


class BitcoinReceiver(CreateableAPIResource, UpdateableAPIResource, DeletableAPIResource, ListableAPIResource):
    def instance_url(self):
        extn = quote_plus(self.id)

        if hasattr(self, 'customer'):
            base = Customer.class_url()
            cust_extn = quote_plus(self.customer)

            return '%s/%s/sources/%s' % (base, cust_extn, extn)
        else:
            base = BitcoinReceiver.class_url()
            return '%s/%s' % (base, extn)

    @classmethod
    def class_url(cls):
        return '/v1/bitcoin/receivers'


class BitcoinTransaction(StripeObject):
    pass


class Product(CreateableAPIResource, UpdateableAPIResource, ListableAPIResource):
    pass


class SKU(CreateableAPIResource, UpdateableAPIResource, ListableAPIResource):
    pass


class Order(CreateableAPIResource, UpdateableAPIResource, ListableAPIResource):
    async def pay(self, idempotency_key=None, **kwargs):
        headers = populate_headers(idempotency_key)
        return await self.request(
            'post', self.instance_url() + '/pay', kwargs, headers)
