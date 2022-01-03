import ccxt
import config

#API to initialize the exchange
def get_exchange():
    # defining the exchange from where we want the data , we are connecting to binance
    # Note : We are not in binanceus
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

#Calculating the supertrend
def supertrend(df , period= 7, multiplier=3):
    hl2=(df['high']+df['low'])/2
    df['atr'] = atr(df,period)
    df['upperband'] = hl2 + (multiplier * df['atr'])
    df['lowerband'] = hl2 - (multiplier * df['atr'])
    df['in_uptrend'] = True

    for current in range(1,len(df.index)):
        #here current is my running index and previous is my previos index ,
        # here i will be comparing my current data with previous data
        previous = current -1

        if df['close'][current] > df['upperband'][previous]:
            df['in_uptrend'][current]= True
        elif df['close'][current] < df['lowerband'][previous]:
            df['in_uptrend'][current] = False
        else:
            df['in_uptrend'][current] = df['in_uptrend'][previous]

            if df['in_uptrend'][current] and df['lowerband'][current] < df['lowerband'][previous]:
                df['lowerband'][current] = df['lowerband'][previous]

            if not df['in_uptrend'][current] and df['upperband'][current] > df['upperband'][previous]:
                df['upperband'][current] = df['upperband'][previous]
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

def check_and_trigger_buy_sell_orders(df,coin_symbol,exchange):
    #Calculating whether we are already in position or not
    in_position = check_in_position(df,coin_symbol,exchange)

    print(f'Checking for buy and sell for {coin_symbol}')
    print(df.tail(2))

    last_row_index = len(df.index) -1
    previous_row_index = last_row_index -1

    decide_position_to_use = calculate_lot_size_for_trade_buy(exchange,coin_symbol)
    #For Buy Order
    if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
        if not in_position:
            print(f'Change to uptrend :  Buy . Going to punch buy order for {coin_symbol} and the quantity is  {decide_position_to_use} ')
            order = exchange.create_market_buy_order(coin_symbol,decide_position_to_use)
            print(order)
            in_position= True
        else :
            print('Already in position , nothng to do')

    #For Sell order
    if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
        if in_position:
            print('Change to downtrend : Sell ')
            free_balance_to_Sell = calculate_free_coins_for_sell(coin_symbol,exchange)
            order = exchange.create_market_sell_order(coin_symbol,free_balance_to_Sell )
            print(order)
            in_position = False
        else:
            print('You arent in position nothing to sell')


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