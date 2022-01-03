import datetime

import schedule
import time
import warnings
import pandas as pd
import config
from datetime import datetime

#To suppress warnings
import helper
warnings.filterwarnings('ignore')

#Option to display all rows
pd.set_option('display.max_rows',None)



def run_bot(trade):
    #Get trade detail from config
    coin_symbol = trade.get('coin_symbol')
    time_frame = config.time_frame

    print(f'fetching new bars for {coin_symbol} {datetime.now().isoformat()}')

    #Fetching the exchange inside bot
    exchange = helper.get_exchange()

    # Getting the ohlcv for the coin on the time frame provided
    bars = exchange.fetch_ohlcv(coin_symbol, timeframe=time_frame, limit=100)
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    # Converting the timestamp into meaningful format
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    super_trend_data = helper.supertrend(df)

    helper.check_and_trigger_buy_sell_orders(super_trend_data,coin_symbol,exchange)

def trade_crypto():
    print(f'==========================Started At==================== {datetime.now().isoformat()}==============')
    for trade in config.trades:
        run_bot(trade)
    print(f'==========================Ended At==================== {datetime.now().isoformat()}==============')

schedule.every(20).seconds.do(trade_crypto)


while True:
    schedule.run_pending()
    time.sleep(1)

