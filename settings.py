import configparser
config = configparser.ConfigParser()
config.read('config.ini')

import keys

#Window settings
window_price_levels = config['Window'].getint('WindowPriceLevels', 50)
    #need to generate this dynamically based on the window size at some point

#Trading settings
api_key = config['Trading'].get('ApiKey', keys.api)
secret_key = config['Trading'].get('SecretKey', keys.secret)

instrument = config['Trading']['Instrument']
tick_size = config['Trading'].getint('TickSize')   #Need to implement dynamic tick sizing
lot_size = config['Trading'].getfloat('LotSize')   #Default order size
lot_increment_size = config['Trading'].getfloat('LotIncrementSize')
pnl_point_mode = config['Trading'].getboolean('PnlPointMode')   #Display PnL in points or currency

#Dom settings
vol_filter = config['Dom'].getint('VolumeFilter')  #Aggregate trade size filter
book_size = config['Dom'].getint('BookSize')
auto_subscribe = config['Dom'].getboolean('AutoSubscribe')
precision = config['Dom'].getint('Precision')  #Decimal point precision
init_trademode = config['Dom'].getboolean('InitTrademode')  #Start program in trade mode
