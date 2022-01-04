import ccxt

import config

exchange = ccxt.binance({
            'apiKey': config.API_KEY,
            'secret': config.API_SECRET
        })
trades = config.trades


def check_in_position(coin_symbol, exchange):
    coin = str(coin_symbol).split('/', 1)
    balances = exchange.fetch_balance()
    assets = balances.get("info").get("balances")
    #last_row_index = len(df.index) - 1
    for asset in assets:
        if asset.get('asset') == coin[0]:
            free = float(asset['free'])
            locked = float(asset['locked'])
            print(f'Free Balacne is {free} and locked is {locked}')
            # Fetching the latest price of coin_symbol(ETH/USDT)
            price = float(exchange.fetchTicker(coin_symbol).get('last'))
            current_position_size = price * (free + locked)
            if current_position_size > 10:
                print(
                    f'You are already in position for {coin_symbol} , free balance {free} and estimated position size {current_position_size}')
                return True
    return False


# for trade in trades:
#     coin_symbol = trade.get('coin_symbol')
#     print(f'Checking if position exists for {coin_symbol} and the value is {check_in_position(coin_symbol, exchange)}')
#     print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
#     print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
#     print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
#     print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

coin_symbol = 'ALGO/USDT'
print(f'Checking if position exists for {coin_symbol} and the value is {check_in_position(coin_symbol, exchange)}')
print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

