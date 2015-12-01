import aiostripe
import asyncio


async def main():
    aiostripe.api_key = 'sk_test_tow8DgveiQpQx7dtNbvC2hU5'

    print('Attempting charge...')

    resp = await aiostripe.Charge.create(
        amount=1000,
        currency='usd',
        card={
            'number': '4242424242424242',
            'exp_month': 10,
            'exp_year': 2016
        },
        description='Hello from aiostripe!'
    )

    print(resp.created)

    print('Success: %r' % (resp, ))

asyncio.get_event_loop().run_until_complete(main())
