import sys
import configparser
config = configparser.ConfigParser()
config.read('config.ini')

import keys

#Window settings
window_price_levels = config['Window'].getint('WindowPriceLevels', 50)
    #need to generate this dynamically based on the window size at some point

#Trading settings
try:
    api_key = config.get('Trading', 'ApiKey', fallback=keys.api)
    secret_key = config.get('Trading', 'SecretKey', fallback=keys.secret)
except configparser.NoOptionError as err:
    print(f"! You have a problem with your API keys: \n\n{err}\n")
    print("Check your config.ini file.\n")
    sys.exit(1)

instrument = config['Trading']['Instrument']
tick_size = config['Trading'].getint('TickSize')   #Need to implement dynamic tick sizing
lot_size = config['Trading'].getfloat('LotSize')   #Default order size
lot_increment_size = config['Trading'].getfloat('LotIncrementSize')
pnl_tick_mode = config['Trading'].getboolean('PnlTickMode')   #Display PnL in points or currency

#Dom settings
vol_filter = config['Dom'].getint('VolumeFilter')  #Aggregate trade size filter
book_size = config['Dom'].getint('BookSize')
auto_subscribe = config['Dom'].getboolean('AutoSubscribe')
precision = config['Dom'].getint('Precision')  #Decimal point precision
init_trademode = config['Dom'].getboolean('InitTrademode')  #Start program in trade mode
