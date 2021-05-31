from tori import *

#FUNCTIONS

def connect():
    global dict_setup
    global subscribed_bool

    dict_setup = False

    if subscribed_bool == False:
        subscribed_bool = True

        #Subscribe to aggregate trade stream
        print("\nSubscribing... - " + time)
        sub_client.subscribe_aggregate_trade_event(instrument, get_trades_callback, error)

        #Start orderbook websocket thread

        #Subscribe to user data
        print("Connecting to user data stream... - " + time)
        listenkey = request_client.start_user_data_stream()
        sub_client.subscribe_user_data_event(listenkey, user_data_callback, error)

    else:
        print("Already running.")

def disconnect():
    global title_instrument_info
    global subscribed_bool

    title_instrument_info = "none"
    subscribed_bool = False
    orderbook_subscribed_bool = False

    print("\n\nDisconnected.\n")
    sub_client.unsubscribe_all()

    #main subscription functionality
def get_trades_callback(data_type: 'SubscribeMessageType', event: 'any'):
    global dict_setup
    global prices
    global global_lastprice
    global title_instrument_info
    global coord
    global last_trade

    coord = int(price_label0["text"]) - global_lastprice

    if data_type == SubscribeMessageType.RESPONSE:
        print("EventID: ", event)

    elif data_type == SubscribeMessageType.PAYLOAD:
        #PrintBasic.print_obj(event)    #keep for full aggtrade payload example

        #set current global_lastprice
        global_lastprice = int(round(event.price, 0))
        #set local price variable
        local_lastprice = global_lastprice
        #update window title ticker info
        title_instrument_info = instrument + " " + str(local_lastprice)

        #Populate price levels dictionary
        if dict_setup == False:
            print("Set up dictionary - " + time + "\n")

            for i in range(0, local_lastprice + local_lastprice):
                #only adding the total level volume information for the moment
                prices[i] = {"volume" : 0, "buy" : 0, "sell" : 0}

            #This and refresh() for us to have a midpoint coord on first startup
            #   in order to avoid refresh() spamming because highlight_trade_price hasn't received
            #   a coord over the auto-recenter trigger
            price_label0["text"] = global_lastprice+ladder_midpoint
            coord = int(price_label0["text"]) - global_lastprice

            dict_setup = True

            refresh()
            highlight_trade_price()
            volume_column_populate(False)
            buy_column_populate(False)
            sell_column_populate(False)

        #add event order quantity to price[volume] dict key
        prices[local_lastprice]["volume"] += round(event.qty, 0)
        last_trade["qty"] = int(round(event.qty, 0))

        if event.isBuyerMaker == False:
            #if buyer
            last_trade["buyer"] = True
            prices[local_lastprice]["buy"] += round(event.qty, 0)
        else:
            #if seller
            last_trade["buyer"] = False
            prices[local_lastprice]["sell"] += round(event.qty, 0)

    else:
        print("Unknown Data:")

def user_data_callback(data_type: 'SubscribeMessageType', event: 'any'):
    if data_type == SubscribeMessageType.RESPONSE:
        print("EventID: ", event)

    elif data_type == SubscribeMessageType.PAYLOAD:
        '''print("\n--------------EVENT--------------")
        PrintBasic.print_obj(event)
        print("------------END EVENT------------")'''

        if event.eventType == "ORDER_TRADE_UPDATE" and event.orderStatus == "NEW":
            #open_orders[event.orderId] = {"price" : event.price, "side" : event.side, "qty" : event.origQty}

            if event.price not in open_orders:
                open_orders[int(event.price)] = {}

            open_orders[event.price]["side"] = event.side

            if "ids" in open_orders[event.price]:
                open_orders[event.price]["ids"].append(event.orderId)
            else:
                open_orders[event.price]["ids"] = []
                open_orders[event.price]["ids"] = [event.orderId]

            if "qty" in open_orders[event.price]:
                open_orders[event.price]["qty"] += event.origQty
            else:
                open_orders[event.price]["qty"] = event.origQty

            print(f"Order {event.side} {event.origQty} at {int(event.price)} placed. - {time}\n")

        if event.eventType == "ORDER_TRADE_UPDATE" and event.orderStatus == "FILLED":
            #Check for matching order id by event.price/open_orders[price]
            for id in list(open_orders[event.price]["ids"]):
                #If event id matches an open_orders id, then delete id from dict
                if id == event.orderId:
                    open_orders[event.price]["ids"].remove(id)

                    #If open_orders is void of ids after this, remove that price level from dict
                    if open_orders[event.price]["ids"] == []:
                        open_orders.pop(event.price, None)
                    #Otherwise just subtract order qty from dict level qty
                    else:
                        open_orders[event.price]["qty"] -= event.origQty

        if event.eventType == "ACCOUNT_UPDATE":
            print("\n-----------POSITIONS-------------")

            for i in range(len(event.positions)):
                if event.positions and event.positions[i].symbol == instrument.upper():
                    #If account update event details open position, add to open_position
                    if event.positions[i].amount != 0:
                        PrintBasic.print_obj(event.positions[i])

                        open_position["entry"] = int(round(event.positions[i].entryPrice, 0))
                        open_position["qty"] = event.positions[i].amount
                        open_position["coord"] = int(price_label0["text"]) - open_position["entry"]
                        print(f"Position: {open_position}")

                    #If account update event details no open position, clear open_position
                    elif event.positions[i].amount == 0:
                        PrintBasic.print_obj(event.positions[i])
                        entry_coord = open_position["coord"]

                        exec(f"price_label{entry_coord}['text'] = '{ladder_dict[entry_coord]}'")
                        exec(f"price_label{entry_coord}['fg'] = 'white'")

                        open_position["entry"] = 0
                        open_position["coord"] = 0
                        open_position["qty"] = 0
                        print(f"Position closed: {open_position}")

            print("\n---------END POSITIONS-----------")

    else:
        print("Unknown Data:")

def error(e: 'BinanceApiException'):
    print(e.error_code + e.error_message)

    #recenter/price populate price axis
def refresh():
    global ladder_midpoint
    global global_lastprice
    global ladder_dict

    label = "price_label{0}"
    vlabel = "volume_label{0}"
    blabel = "buy_label{0}"
    slabel = "sell_label{0}"
    olabel = "order_label{0}"

    #populate the ladder cell dictionary
    for i in range(window_price_levels):
        ladder_dict[i] = global_lastprice+ladder_midpoint-i

    #write dictionary values to frame
    for i in range(window_price_levels-1, -1, -1):
        eval(label.format(i))["text"] = ladder_dict[i]
        eval(vlabel.format(i))["text"] = str(prices[ladder_dict[i]]["volume"])[:-2]
        eval(blabel.format(i))["text"] = str(prices[ladder_dict[i]]["buy"])[:-2]
        eval(slabel.format(i))["text"] = str(prices[ladder_dict[i]]["sell"])[:-2]
        '''if prices[ladder_dict[i]]["order"]['qty'] > 0:
            eval(olabel.format(i))["text"] = str(f"%.{precision}f" % prices[ladder_dict[i]]["order"]["qty"])
        else:
            eval(olabel.format(i))["text"] = ""'''

    print("Refresh - " + time)

    #volume cell update
def volume_column_populate(clean):
    global subscribed_bool
    global global_lastprice
    global ladder_dict
    global coord

    label = "volume_label{0}"

    eval(label.format(coord))["text"] = str(prices[ladder_dict[coord]]["volume"])[:-2]

    #OLD
    '''for i in range(0, window_price_levels):
        if subscribed_bool == True:
            #print(str(prices[ladder_dict[i]]["volume"]))
            eval(label.format(i))["text"] = str(prices[ladder_dict[i]]["volume"])[:-2]'''

    if clean == False:
        root.after(100, volume_column_populate, False)

def buy_column_populate(clean):
    global subscribed_bool
    global global_lastprice
    global ladder_dict
    global coord

    label = "buy_label{0}"

    eval(label.format(coord))["text"] = str(prices[ladder_dict[coord]]["buy"])[:-2]

    if clean == False:
        root.after(100, buy_column_populate, False)

def sell_column_populate(clean):
    global subscribed_bool
    global global_lastprice
    global ladder_dict
    global coord

    label = "sell_label{0}"

    eval(label.format(coord))["text"] = str(prices[ladder_dict[coord]]["sell"])[:-2]

    if clean == False:
        root.after(100, sell_column_populate, False)

def highlight_trade_price():
    global global_lastprice
    global prev_highlight_price
    global coord
    global prev_coord
    global last_trade

    if dict_setup == True:
        #If there is an open position, mark it at entry_coord location
        if open_position["qty"] != 0:
            entry_coord = open_position["coord"]
            e = open_position["entry"]
            q = open_position["qty"]

            if entry_coord >= 0 and entry_coord <= (window_price_levels - 1):
                if open_position["qty"] > 0:
                    exec(f"price_label{entry_coord}['bg'] = 'mediumpurple'")

                elif open_position["qty"] < 0:
                    exec(f"price_label{entry_coord}['bg'] = 'firebrick'")

                exec(f"price_label{entry_coord}['text'] = '{e} {q}'")

        #Need to be able to remove position marking dynamically as well!

        #Mark last trade qty and side on price axis
        if last_trade["qty"] > vol_filter:
            exec(f"price_label{coord}['text'] = last_trade['qty']")

            if last_trade["buyer"]:
                exec(f"price_label{coord}['fg'] = 'lime'")
            else:
                exec(f"price_label{coord}['fg'] = 'red'")

        #Highlight current trade price coord on axis
        exec(f"price_label{coord}['bg'] = 'blue'")
        exec(f"buy_label{coord}['bg'] = 'silver'")
        exec(f"sell_label{coord}['bg'] = 'silver'")

        #If new price from last coord, reset previous coord's label style
        if coord != prev_coord:
            exec(f"price_label{prev_coord}['text'] = ladder_dict[prev_coord]")

            exec(f"price_label{prev_coord}['bg'] = 'gray'")
            exec(f"price_label{prev_coord}['fg'] = 'white'")
            exec(f"buy_label{prev_coord}['bg'] = 'gainsboro'")
            exec(f"sell_label{prev_coord}['bg'] = 'gainsboro'")

    prev_coord = coord

    if dict_setup == True and (coord < 6 or coord > (window_price_levels-6)):
        refresh()

    root.after(100, highlight_trade_price)

def clean_volume():
    blabel = "buy_label{0}"
    slabel = "sell_label{0}"

    for i in range(len(prices)):
        #prices[i]["volume"] = 0
        prices[i]["buy"] = 0
        prices[i]["sell"] = 0

    for i in range(window_price_levels):
        eval(blabel.format(i))["text"] = ""
        eval(slabel.format(i))["text"] = ""

    print("clean volume - " + time)

def place_order(coord, side):
    if subscribed_bool == True and dict_setup == True and trade_mode == True:
        price = ladder_dict[coord]

        #Send order to binance
        if side == "BUY":
            result = request_client.post_order(symbol=instrument, side=OrderSide.BUY,
                ordertype=OrderType.LIMIT, price=price, quantity=order_size, timeInForce=TimeInForce.GTC,)

            #eval(label.format(coord))["text"] = str(open_orders[i]["qty"])
            #open_orders[event.orderId]["qty"] += order_size

        elif side == "SELL":
            result = request_client.post_order(symbol=instrument, side=OrderSide.SELL,
                ordertype=OrderType.LIMIT, price=price, quantity=order_size, timeInForce=TimeInForce.GTC,)

        print(f"Order {side} {order_size} at {price} sent to exchange. - {time}\n")

def cancel_order(coord):
    if subscribed_bool == True and dict_setup == True and trade_mode == True:
        price = ladder_dict[coord]
        label = "order_label{0}"

        #For every order id at logged at a particular price level, cancel.
        for id in list(open_orders[price]["ids"]):
            result = request_client.cancel_order(symbol=instrument, orderId=id)

            #Double check that order has been cancelled at exchange before removing from list
            #Ideally there should be a try: & except: here
            if result.status == "CANCELED" and result.orderId == id:
                open_orders[price]["ids"].remove(id)

        #Once every id is deleted at a price level, remove level from open orders list
        #Another try: & except: here.
        if open_orders[price]["ids"] == []:
            open_orders.pop(price, None)

        #Reset label text
        eval(label.format(coord))["text"] = ""

        print(f"after cancel: {open_orders}")

def cancel_all():
    label = "order_label{0}"

    request_client.cancel_all_orders(symbol=instrument)

    for order in list(open_orders):
        coord = int(price_label0["text"]) - order

        open_orders.pop(order, None)
        eval(label.format(coord))["text"] = ""

def flatten():
    #I need to be built
    pass

def trade_mode_swap():
    global trade_mode

    if trade_mode == False:
        trade_mode = True
        trademodebutton["bg"] = "lightcoral"
        print("Trade mode activated.")

    else:
        trade_mode = False
        trademodebutton["bg"] = "whitesmoke"
        print("Trade mode disabled.")
