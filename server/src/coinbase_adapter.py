import json

import cbpro
import result
from logger import logger
from pyrsistent import PRecord, field


class CoinbaseKeys(PRecord):
    passphrase = field(type=str, mandatory=True)
    b64secret = field(type=str, mandatory=True)
    key = field(type=str, mandatory=True)


def get_authentication_keys(path: str, environment: str) -> CoinbaseKeys:
    """
    expects coinbase keys to be found in config/authentication.json
    expects authentication.json to have the following structure:
    {
        "sandbox": {
            "passphrase": "",
            "b64secret": "",
            "key": ""
        },
        "production": {
            "passphrase": "",
            "b64secret": "",
            "key": ""
        }
    }
    """
    with open('config/authentication.json', 'r') as reader:
        auth_keys = json.load(reader)[environment]
        return CoinbaseKeys(
            passphrase=auth_keys['passphrase'],
            b64secret=auth_keys['b64secret'],
            key=auth_keys['key']
        )


keys = get_authentication_keys('config/authentication.json', 'production')

# auth_client = cbpro.AuthenticatedClient(key, b64secret, passphrase)
# Use the sandbox API (requires a different set of API access credentials)
auth_client = cbpro.AuthenticatedClient(
    keys.key,
    keys.b64secret,
    keys.passphrase,
    api_url="https://api.pro.coinbase.com"
)

# fills_gen = auth_client.get_fills()
# all_fills = list(fills_gen)
# print(all_fills)

# response = auth_client.buy(price='100.00',  # USD
#                            size='0.001',  # BTC
#                            order_type='limit',
#                            product_id='BTC-USD')

# print(response)
# order_id = response['id']


def limit_sell(product, price, size, client):
    response = client.sell(price=price,  # USD
                           size=size,  # BTC
                           order_type='limit',
                           product_id=product)
    if 'message' in response:
        return result.Error(response['message'])
    return response


response = limit_sell(product='BTC-USD', price='15000.0', size='.001', client=auth_client)
logger.log(f'response: {response}')

# cancel_response = auth_client.cancel_order(order_id)
# print(cancel_response)

# get_orders = auth_client.get_orders()
# print(get_orders)

# all_orders = list(get_orders)
# print(all_orders)
# print(f'\n\n')

# accounts = auth_client.get_accounts()
# print(accounts)

# order_book = cbpro.OrderBook(product_id='BTC-USD')
# order_book.start()
