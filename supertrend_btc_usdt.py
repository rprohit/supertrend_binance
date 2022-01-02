import ccxt
import schedule
import time
import warnings

import config

warnings.filterwarnings('ignore')

import pandas as pd
pd.set_option('display.max_rows',None)

#Global Variables
lot_size = 0.00211 #TODO
time_frame = '1m'
coin_symbol = 'BTC/USDT'

#defining the exchange from where we want the data , we are connecting to binance
#Note : We are not in binanceus
exchange = ccxt.binance({
    'apiKey': config.API_KEY,
    'secret': config.API_SECRET
})
#print(f'Balance {exchange.fetch_balance()}')
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

#Fetch Buy or Sell Signals
#todo Code the in_position logic as current implementation will always reset to false if the server is restarted
in_position= False

def check_buy_sell_signals(df,coin_symbol):
    global in_position
    print(f'Checking for buy and sell for {coin_symbol}')
    print(df.tail(2))
    last_row_index = len(df.index) -1
    previous_row_index = last_row_index -1

    if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
        if not in_position:
            print('Change to uptrend :  Buy ')
            #order = exchange.create_market_buy_order(coin_symbol,lot_size)
            #print(order)
            in_position= True
        else :
            print('Already in position , nothng to do')
    if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
        if in_position:
            print('Change to downtrend : Sell ')
            #order = exchange.create_market_sell_order(symbol=coin_symbol, )
            #print(order)
            in_position = False
        else:
            print('You arent in position nothing to sell')




#API method to fetch the candles

def run_bot1():
    #print(f'fetching new bars for {datetime.now().isoformat()}')
    # Getting the ohlcv for ETH/USDT on daily time frame
    bars = exchange.fetch_ohlcv(coin_symbol, timeframe=time_frame, limit=100)
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    # Converting the timestamp into meaningful format
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    #print(df)
    super_trend_data = supertrend(df)
    #print(super_trend_data)

    check_buy_sell_signals(super_trend_data,coin_symbol)


schedule.every(30).seconds.do(run_bot1)


while True:
    schedule.run_pending()
    time.sleep(1)

