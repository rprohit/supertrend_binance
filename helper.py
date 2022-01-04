import ccxt
import config

#API to initialize the exchange
exchange = None
def get_exchange():
    # defining the exchange from where we want the data , we are connecting to binance
    # Note : We are not in binanceus
    global exchange
    if exchange is None:
        exchange = ccxt.binance({
            'apiKey': config.API_KEY,
            'secret': config.API_SECRET
        })
    # print(f'Balance {exchange.fetch_balance()}')
    return exchange

#Calculating True Range
def tr(df):
    df['previous_close'] = df['close'].shift(1)
    df['high-low'] = df['high'] -df['low']
    df['high-pc'] = abs(df['high'] -df['previous_close'])
    df['low-pc'] = abs(df['low'] -df['previous_close'])
    tr = df[['high-low','high-pc','low-pc']].max(axis=1)
    return tr

#Calculating average true range
def atr(df,period=14):
    #adding true range in dataframe
    df['tr'] = tr(df)
    #formula for atr
    the_atr = df['tr'].rolling(period).mean()
    return the_atr
    #df['atr'] = the_atr

#Calculating the supertrend 1
def supertrend_st1(df , period= 7, multiplier=3):
    hl2=(df['high']+df['low'])/2
    df['atr_st1'] = atr(df,period)
    df['upperband_st1'] = hl2 + (multiplier * df['atr_st1'])
    df['lowerband_st1'] = hl2 - (multiplier * df['atr_st1'])
    df['in_uptrend_st1'] = True

    for current in range(1,len(df.index)):
        #here current is my running index and previous is my previos index ,
        # here i will be comparing my current data with previous data
        previous = current -1

        if df['close'][current] > df['upperband_st1'][previous]:
            df['in_uptrend_st1'][current]= True
        elif df['close'][current] < df['lowerband_st1'][previous]:
            df['in_uptrend_st1'][current] = False
        else:
            df['in_uptrend_st1'][current] = df['in_uptrend_st1'][previous]

            if df['in_uptrend_st1'][current] and df['lowerband_st1'][current] < df['lowerband_st1'][previous]:
                df['lowerband_st1'][current] = df['lowerband_st1'][previous]

            if not df['in_uptrend_st1'][current] and df['upperband_st1'][current] > df['upperband_st1'][previous]:
                df['upperband_st1'][current] = df['upperband_st1'][previous]
    return df

#Calculating the supertrend 2
def supertrend_st2(df , period= 7, multiplier=3):
    hl2=(df['high']+df['low'])/2
    df['atr_st2'] = atr(df,period)
    df['upperband_st2'] = hl2 + (multiplier * df['atr_st2'])
    df['lowerband_st2'] = hl2 - (multiplier * df['atr_st2'])
    df['in_uptrend_st2'] = True

    for current in range(1,len(df.index)):
        #here current is my running index and previous is my previos index ,
        # here i will be comparing my current data with previous data
        previous = current -1

        if df['close'][current] > df['upperband_st2'][previous]:
            df['in_uptrend_st2'][current]= True
        elif df['close'][current] < df['lowerband_st2'][previous]:
            df['in_uptrend_st2'][current] = False
        else:
            df['in_uptrend_st2'][current] = df['in_uptrend_st2'][previous]

            if df['in_uptrend_st2'][current] and df['lowerband_st2'][current] < df['lowerband_st2'][previous]:
                df['lowerband_st2'][current] = df['lowerband_st2'][previous]

            if not df['in_uptrend_st2'][current] and df['upperband_st2'][current] > df['upperband_st2'][previous]:
                df['upperband_st2'][current] = df['upperband_st2'][previous]
    return df

# Check in_position for symbol
def check_in_position(df,coin_symbol, exchange):
    coin = str(coin_symbol).split('/',1)
    balances = exchange.fetch_balance()
    assets = balances.get("info").get("balances")
    last_row_index = len(df.index) - 1
    for asset in assets:
        if asset.get('asset') == coin[0]:
            free = float(asset['free'])
            print(f'Free Balacne is {free}')
            #Fetching the latest price of coin_symbol(ETH/USDT)
            price = float(exchange.fetchTicker(coin_symbol).get('last'))
            current_position_size = price *free
            if current_position_size > 10:
                print(f'You are already in position for {coin_symbol} , free balance {free} and estimated position size {current_position_size}')
                return True
    return False


def calculate_lot_size_for_trade_buy(exchange,coin_symbol):
     #Fetching available usdt as balance
    #balance = float(exchange.fetch_balance().get('USDT').get('free')) This would always give the percentage from last trade we want a hardcoded value
    total_balance_for_supertrend = config.total_balance_for_supertrend
    #print(f' Available USDT for Supertrend strategy is {total_balance_for_supertrend}')

    # set the percentage or fraction you want to invest in each order
    portion_balance = float(total_balance_for_supertrend) * (config.per_per_trade/100)

    #Fetching current price of coin_symbol
    price = float(exchange.fetchTicker(coin_symbol).get('last'))
    print(f' Last price for {coin_symbol} is {price}')

    decide_position_to_use = portion_balance / price
    print(f'Unrounded {decide_position_to_use}')
    decide_position_to_use_rounded = format_num_filter(decide_position_to_use)

    print(f' Decided position for {coin_symbol} is {decide_position_to_use_rounded}')
    return decide_position_to_use

def calculate_free_coins_for_sell(coin_symbol,exchange):
    free = 0
    balances = exchange.fetch_balance()
    assets = balances.get("info").get("balances")
    coin = str(coin_symbol).split('/', 1)
    for asset in assets:
        if asset.get('asset') == coin[0]:
            free = float(asset['free'])
            return free
    return free

#This strategy is complete supertrend startegy - buy ansd sell will be punched based on supertrend only
def check_and_trigger_buy_sell_orders(df,coin_symbol,exchange):
    #Calculating whether we are already in position or not
    in_position = check_in_position(df,coin_symbol,exchange)

    print(f'Checking for buy and sell for {coin_symbol}')
    print(df.tail(2))

    last_row_index = len(df.index) -1
    previous_row_index = last_row_index -1

    decide_position_to_use = calculate_lot_size_for_trade_buy(exchange,coin_symbol)
    #TODO - some refactoring
    #price_usdt = float(exchange.fetchTicker('USDT/USDT').get('last'))
    free_usdt = calculate_free_coins_for_sell('USDT/USDT',exchange)
    #portion_balance = float(config.total_balance_for_supertrend) * (config.per_per_trade / 100)
    #For Buy Order
    #if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
    if df['in_uptrend_st1'][last_row_index] and df['in_uptrend_st2'][last_row_index]:
        if not in_position and df['ema_in_uptrend'][last_row_index] and (free_usdt >60): #TODO remove hardcoding
            print(f'Change to uptrend :  Buy . Going to punch buy order for {coin_symbol} and the quantity is  {decide_position_to_use} ')
            order = exchange.create_market_buy_order(coin_symbol,decide_position_to_use)
            print(order)
            in_position= True
        else :
            print('Already in position , nothng to do')

    #For Sell order if any of supertrend is in down trend we will sell the holdings
    if (not df['in_uptrend_st1'][last_row_index]) or (not df['in_uptrend_st2'][last_row_index]):
        if in_position:
            print('Change to downtrend : Sell ')
            free_balance_to_Sell = calculate_free_coins_for_sell(coin_symbol,exchange)
            order = exchange.create_market_sell_order(coin_symbol,free_balance_to_Sell )
            print(order)
            in_position = False
        else:
            print('You arent in position nothing to sell')

#This strategy is based on 1:2 profit and loss - We will book profit on 5% above the buying price and stop loss will be of 2%
def check_and_trigger_buy_sell_orders_risk_reward(df,coin_symbol,exchange):

    #Calculating whether we are already in position or not
    in_position = check_in_position(df,coin_symbol,exchange)

    print(f'Checking for buy and sell for {coin_symbol}')
    print(df.tail(2))

    last_row_index = len(df.index) -1
    previous_row_index = last_row_index -1

    decide_position_to_use = calculate_lot_size_for_trade_buy(exchange,coin_symbol)
    #TODO - some refactoring
    #price_usdt = float(exchange.fetchTicker('USDT/USDT').get('last'))
    free_usdt = calculate_free_coins_for_sell('USDT/USDT',exchange)
    #portion_balance = float(config.total_balance_for_supertrend) * (config.per_per_trade / 100)
    #For Buy Order
    #if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
    if df['in_uptrend_st1'][last_row_index] and df['in_uptrend_st2'][last_row_index] and ((not df['in_uptrend_st1'][previous_row_index] and df['in_uptrend_st1'][last_row_index]) or(not df['in_uptrend_st2'][previous_row_index] and df['in_uptrend_st2'][last_row_index])):
        if not in_position and df['ema_in_uptrend'][last_row_index] and (free_usdt >60): #TODO remove hardcoding
            print(f'Change to uptrend :  Buy . Going to punch buy order for {coin_symbol} and the quantity is  {decide_position_to_use} ')
            order_buy_order = exchange.create_market_buy_order(coin_symbol,decide_position_to_use)
            print(order_buy_order)

            #Placing OCO sell order with 5% profit -
            market = exchange.market(coin_symbol)
            amount = order_buy_order.get('amount')
            price = order_buy_order.get('average') * 1.05
            stop_price = order_buy_order.get('average') * 0.971
            stop_limit_price = order_buy_order.get('average') * 0.97

            response = exchange.private_post_order_oco({
                'symbol': market['id'],
                'side': 'SELL',  # SELL, BUY
                'quantity': exchange.amount_to_precision(coin_symbol, amount),
                'price': exchange.price_to_precision(coin_symbol, price),
                'stopPrice': exchange.price_to_precision(coin_symbol, stop_price),
                'stopLimitPrice': exchange.price_to_precision(coin_symbol, stop_limit_price),
                # If provided, stopLimitTimeInForce is required
                'stopLimitTimeInForce': 'GTC',  # GTC, FOK, IOC
                # 'listClientOrderId': exchange.uuid(),  # A unique Id for the entire orderList
                # 'limitClientOrderId': exchange.uuid(),  # A unique Id for the limit order
                # 'limitIcebergQty': exchangea.amount_to_precision(symbol, limit_iceberg_quantity),
                # 'stopClientOrderId': exchange.uuid()  # A unique Id for the stop loss/stop loss limit leg
                # 'stopIcebergQty': exchange.amount_to_precision(symbol, stop_iceberg_quantity),
                # 'newOrderRespType': 'ACK',  # ACK, RESULT, FULL
            })
            print(f' OCO resposne is  {response}')
            # #Placing stop loss order -
            # limit_price_sl = order_buy_order.get('average') *0.97
            # stopPrice_sl = order_buy_order.get('average') *0.98 # If price fall below this , stop price a limit order to sell all the qyantities will be placed
            # params = {'stopPrice': stopPrice_sl}
            # order_stop_loss = exchange.create_order(coin_symbol, 'STOP_LOSS_LIMIT', 'sell', order_buy_order.get('amount'), limit_price_sl, params)
            # print(f' Stop loss order is {order_stop_loss}')
            # #Placing the take profit order
            # limit_price_profit = order_buy_order.get('average') * 1.05
            # #stopPrice_sl_profit = order_buy_order.get('average') * 1.05  # If price fall below this , stop price a limit order to sell all the qyantities will be placed
            # print('Creating the take profit order============================')
            # print(f'Creating the take profit order for {order_buy_order.get("amount")} quantities at price {limit_price_profit}')
            # order_take_profit = exchange.create_limit_sell_order(coin_symbol, order_buy_order.get('amount'),
            #                                                    limit_price_profit)


            in_position= True
        else :
            print('Already in position , nothng to do')

    #For Sell order if any of supertrend is in down trend we will sell the holdings
    # if (not df['in_uptrend_st1'][last_row_index]) or (not df['in_uptrend_st2'][last_row_index]):
    #     if in_position:
    #         print('Change to downtrend : Sell ')
    #         free_balance_to_Sell = calculate_free_coins_for_sell(coin_symbol,exchange)
    #         order = exchange.create_market_sell_order(coin_symbol,free_balance_to_Sell )
    #         print(order)
    #         in_position = False
    #     else:
    #         print('You arent in position nothing to sell')


#dynamic rounding for crypto
def format_num_filter(number):
    if 5>number >= 1 :
        return round(number,1)
    elif 1 > number and number>=0.1 :
        return  round(number,2)
    elif 0.1 >number and number>=0.01:
        return round(number,3)
    elif 0.01 > number and number>= 0.001 :
        return round(number,4)
    elif 0.001 > number and number>= 0.0001 :
        return round(number,5)
    elif 0.0001 > number and number>= 0.00001 :
        return round(number,6)
    elif 0.00001 > number and number>= 0.000001 :
        return round(number,7)
    elif 0.000001 > number and number>= 0.0000001 :
        return round(number,8)
    else:
        return round(number)

#API to add SMA
def add_sma(df,period = 14):
    df['sma'] = df['close'].rolling(period).mean()
    df['sma_in_uptrend'] = True
    for current in range(1, len(df.index)):
        previous = current - 1
        if df['sma'][current] > df['sma'][previous]:
            df['sma_in_uptrend'][current] = True
        elif df['sma'][current] < df['sma'][previous]:
            df['sma_in_uptrend'][current] = False
        else:
            df['sma_in_uptrend'][current] =df['sma_in_uptrend'][previous]
    return df

#API to Add EMA
def add_ema(df,period = 14):
    df['ema'] = df['close'].ewm(period).mean()
    df['ema_in_uptrend'] = True
    for current in range(1, len(df.index)):
        previous = current - 1
        if df['ema'][current] > df['ema'][previous]:
            df['ema_in_uptrend'][current] = True
        elif df['ema'][current] < df['ema'][previous]:
            df['ema_in_uptrend'][current] = False
        else:
            df['ema_in_uptrend'][current] = df['ema_in_uptrend'][previous]
    return df

