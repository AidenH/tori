#Window settings
window_price_levels = 50    #Determines height of window,
    #need to generate this dynamically based on the window size at some point

#Trading settings
instrument = "ethusdt"
order_size = 0.01   #Default order size
add_lot_size = 0.01
pnl_point_mode = True   #Display PnL in points or currency

#Dom settings
vol_filter = 5  #Aggregate trade size filter
book_size = 5
auto_subscribe = True
precision = 2   #Decimal point precision
