import aiostripe
import asyncio


async def main():
    aiostripe.api_key = 'tGN0bIwXnHdwOa85VABjPdSn8nWY7G7I'

    print('Attempting charge...')

    resp = await aiostripe.Charge.create(
        amount=200,
        currency='usd',
        card={
            'number': '4242424242424242',
            'exp_month': 10,
            'exp_year': 2014
        },
        description='customer@gmail.com'
    )

    print('Success: %r' % (resp, ))

asyncio.get_event_loop().run_until_complete(main())
