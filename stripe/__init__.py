# Stripe Python bindings
# API docs at http://stripe.com/docs/api
# Authors:
# Patrick Collison <patrick@stripe.com>
# Greg Brockman <gdb@stripe.com>
# Andrew Metcalf <andrew@stripe.com>

# Configuration variables

api_key = None
api_base = 'https://api.stripe.com'
upload_api_base = 'https://uploads.stripe.com'
api_version = None
verify_ssl_certs = True
default_http_client = None

# Resource
from stripe.resource import (  # noqa
    Account,
    ApplicationFee,
    Balance,
    BalanceTransaction,
    BankAccount,
    BitcoinReceiver,
    BitcoinTransaction,
    Card,
    Charge,
    Coupon,
    Customer,
    Dispute,
    Event,
    FileUpload,
    Invoice,
    InvoiceItem,
    Order,
    Plan,
    Product,
    Recipient,
    Refund,
    SKU,
    Subscription,
    Token,
    Transfer)
# Error imports.  Note that we may want to move these out of the root
# namespace in the future and you should prefer to access them via
# the fully qualified `stripe.error` module.

from stripe.error import (  # noqa
    APIConnectionError,
    APIError,
    AuthenticationError,
    RateLimitError,
    CardError,
    InvalidRequestError,
    StripeError)
