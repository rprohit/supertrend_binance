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
pd.set_option('display.max_columns',None)



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

    with_super_trend_data_st1 = helper.supertrend_st1(df,21,4)
    with_super_trend_data_st2 = helper.supertrend_st2(with_super_trend_data_st1,21,2)

    #with_sma_50_day = helper.add_sma(with_super_trend_data,50)
    #with_ema_55_day = helper.add_ema(with_super_trend_data,200)
    with_ema_55_day = helper.add_ema(with_super_trend_data_st2,config.ema_period)

    helper.check_and_trigger_buy_sell_orders(with_ema_55_day,coin_symbol,exchange)

def trade_crypto():
    try:

        print(f'==========================Started At==================== {datetime.now().isoformat()}========================================================')
        for trade in config.trades:
            print(f"=============================================================Starting for Trade {trade.get('coin_symbol')}==========================")
            run_bot(trade)
            print(f"=============================================================Ending for Trade {trade.get('coin_symbol')}==========================")

            time.sleep(0.5)
        print(f'==========================Ended At==================== {datetime.now().isoformat()}===========================================================')
    except Exception as e:
        print("Exception raised: {}".format(e))
        print(
            f'=================================Exception Raised in the code hence adding a delay of 3 minutes to retry =============')
        time.sleep(1)
        print(f'=================================Going to call the scheduler again ========================================')




def start_bot():
    schedule.every(150).seconds.do(trade_crypto)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    print(f'=================================Starting My Supertrend trading bot  - HANDLER - process...{datetime.now().isoformat()}=============')
    start_bot()