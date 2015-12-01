import aiostripe
from aiostripe.test.helper import StripeResourceTest, DUMMY_CARD


class RecipientTest(StripeResourceTest):
    async def test_list_recipients(self):
        await aiostripe.Recipient.list()

        self.requestor_mock.request.assert_called_with('get', '/v1/recipients',
                                                       {})

    async def test_recipient_transfers(self):
        recipient = aiostripe.Recipient(id='rp_transfer')

        await recipient.transfers()

        self.requestor_mock.request.assert_called_with('get', '/v1/transfers',
                                                       {'recipient': 'rp_transfer'})

    async def test_recipient_add_card(self):
        recipient = aiostripe.Recipient.construct_from({
            'id': 'rp_add_card',
            'sources': {
                'object': 'list',
                'url': '/v1/recipients/rp_add_card/sources',
            },
        }, 'api_key')

        await recipient.sources.create(card=DUMMY_CARD)

        self.requestor_mock.request.assert_called_with('post', '/v1/recipients/rp_add_card/sources',
                                                       {
                                                           'card': DUMMY_CARD,
                                                       }, None)

    async def test_recipient_update_card(self):
        card = aiostripe.Card.construct_from({
            'recipient': 'rp_update_card',
            'id': 'ca_update_card',
        }, 'api_key')
        card.name = 'The Best'

        await card.save()

        self.requestor_mock.request.assert_called_with('post', '/v1/recipients/rp_update_card/cards/ca_update_card',
                                                       {
                                                           'name': 'The Best',
                                                       }, None)

    async def test_recipient_delete_card(self):
        card = aiostripe.Card.construct_from({
            'recipient': 'rp_delete_card',
            'id': 'ca_delete_card',
        }, 'api_key')

        await card.delete()

        self.requestor_mock.request.assert_called_with('delete', '/v1/recipients/rp_delete_card/cards/ca_delete_card',
                                                       {}, None)
