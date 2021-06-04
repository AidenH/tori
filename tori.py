from datetime import datetime
import tkinter as tk
import threading
from concurrent.futures import ThreadPoolExecutor
import asyncio
import time as t

from binance_f import RequestClient
from binance_f import SubscriptionClient
from binance_f.constant.test import *
from binance_f.model import *
from binance_f.exception.binanceapiexception import BinanceApiException
from binance_f.base.printobject import *

import keys
from settings import *


#Root environment variables
wwidth = 400
wheight = 988
font = "arial 7 bold"
title_instrument_info = "none"

#Dom-related variables
dict_setup = False
ladder_midpoint = 23
subscribed_bool = False
orderbook_subscribed_bool = False
global_lastprice = 0
prev_coord = 0
coord = 0
prices = {}
small_book = {0 : {"bids" : 0, "asks" : 0}}
last_trade = {"qty" : 0, "buyer" : False}

#Trading variables
trade_mode = False
open_orders = {}
open_position = {"entry" : 0, "coord" : 0, "qty" : 0, "pnl": 0}

sub_client = SubscriptionClient(api_key=keys.api, secret_key=keys.secret)
request_client = RequestClient(api_key=keys.api, secret_key=keys.secret)

ladder_dict = {}
for i in range(window_price_levels):
    ladder_dict[i] = 0


#FUNCTIONS

def connect():
    global dict_setup
    global subscribed_bool

    dict_setup = False

    if subscribed_bool == False:
        subscribed_bool = True

        #Subscribe to aggregate trade stream
        print("\nSubscribing... - " + time)
        agg_result = sub_client.subscribe_aggregate_trade_event(instrument,
            get_trades_callback, error)

        #Start orderbook websocket thread

        #Subscribe to user data
        print("Connecting to user data stream... - " + time)
        listenkey = request_client.start_user_data_stream()
        data_result = sub_client.subscribe_user_data_event(listenkey, user_data_callback, error)

    if agg_result and data_result:
        return True

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

    #get aggregate trades
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

            #tick_size other than 1 not yet working.
            #Subscriptionprocess error on start.
            for i in range(0, local_lastprice + local_lastprice, tick_size):
                #Init price level volume data
                prices[i] = {"volume" : 0, "buy" : 0, "sell" : 0}

            #This and refresh() for us to have a midpoint coord on first startup
            #   in order to avoid refresh() spamming because highlight_trade_price hasn't received
            #   a coord outside the auto-recenter trigger zones
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

    #user data for position updates, balance etc.
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
    asklabel = "ask_label{0}"
    bidlabel = "bid_label{0}"

    #populate the ladder cell dictionary
    for i in range(window_price_levels):
        ladder_dict[i] = global_lastprice+ladder_midpoint-i

        eval(asklabel.format(i))["text"] = ""
        eval(bidlabel.format(i))["text"] = ""

        eval(olabel.format(i))["text"] = ""

    #write dictionary values to frame
    for i in range(window_price_levels-1, -1, -1):
        eval(label.format(i))["text"] = ladder_dict[i]
        eval(vlabel.format(i))["text"] = str(prices[ladder_dict[i]]["volume"])[:-2]
        eval(blabel.format(i))["text"] = str(prices[ladder_dict[i]]["buy"])[:-2]
        eval(slabel.format(i))["text"] = str(prices[ladder_dict[i]]["sell"])[:-2]

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
        if side == "BUY" and order_size > 0:
            result = request_client.post_order(symbol=instrument, side=OrderSide.BUY,
                ordertype=OrderType.LIMIT, price=price, quantity="%.2f"%order_size,
                    timeInForce=TimeInForce.GTC,)

            print(f"\nOrder {side} {order_size} at {price} sent to exchange. - {time}")

        elif side == "SELL" and order_size > 0:
            result = request_client.post_order(symbol=instrument, side=OrderSide.SELL,
                ordertype=OrderType.LIMIT, price=price, quantity="%.2f"%order_size,
                    timeInForce=TimeInForce.GTC,)

            print(f"\nOrder {side} {order_size} at {price} sent to exchange. - {time}")

        else:
            print(f"\nError: Order {side} {order_size} at {price} was not sent. - {time}")

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
        print("\nTrade mode activated.")

    else:
        trade_mode = False
        trademodebutton["bg"] = "whitesmoke"
        print("\nTrade mode disabled.")

def modqty(type):
    global order_size

    if type == "add":
        order_size += add_lot_size
        lotqty["text"] = f"Qty: {'%.2f'%order_size}"
    elif type == "clear":
        order_size = 0
        lotqty["text"] = f"Qty: {'%.2f'%order_size}"

#THREADS
def listener():
    global global_lastprice
    label = "order_label{0}"

    if subscribed_bool == True and dict_setup == True:
        for i in open_orders:
            coord = int(price_label0["text"]) - i

            if coord >= 0 and coord <= window_price_levels-1:

                #If order is buy
                if open_orders[i]["side"] == "BUY":
                    pass
                    eval(label.format(coord))["text"] = open_orders[i]["qty"]
                    eval(label.format(coord))["fg"] = "blue"

                if open_orders[i]["side"] == "SELL":
                    eval(label.format(coord))["text"] = open_orders[i]["qty"]
                    eval(label.format(coord))["fg"] = "maroon"

        #LONG
        if open_position["qty"] > 0:
            open_position["pnl"] = round((global_lastprice * open_position["qty"])
                - (open_position["entry"] * open_position["qty"]), 3)

            #check whether pnl should be in point mode or cash mode
            if pnl_point_mode == False:
                pnllabel["text"] = "PnL: " + str(open_position["pnl"])
            else:
                pnllabel["text"] = "PnL: " + str(global_lastprice - open_position["entry"]) + "pt"

            positionlabel["text"] = f"Position: {open_position['qty']}"

        #SHORT
        elif open_position["qty"] < 0:
            pass

        #NO POSITION
        else:
            positionlabel["text"] = "Position: ---"
            pnllabel["text"] = "PnL: ---"

    root.after(500, listener)

def orderbook_listener():
    #_executor = ThreadPoolExecutor(1)

    #Populate orderbook dictionary
    async def get_request():
        result = request_client.get_order_book(instrument, 500)

        await asyncio.sleep(0.01)

        for price in small_book:
            coord = price_label0["text"] - price
            if coord >= 0 and coord < window_price_levels-1:
                eval(blabel.format(coord))["text"] = ""
                eval(alabel.format(coord))["text"] = ""

        small_book.clear()

        for i in result.bids:
            price = int(round(float(i.price), 0))
            qty = int(round(float(i.qty), 0))

            if price < (global_lastprice - book_size):
                break

            if price not in small_book:
                small_book[price] = {}

            try:
                small_book[price]["bids"] += qty
            except:
                small_book[price]["bids"] = 0

        for i in result.asks:
            price = int(round(float(i.price), 0))
            qty = int(round(float(i.qty), 0))

            if price > (global_lastprice + book_size):
                break

            if price not in small_book:
                small_book[price] = {}

            try:
                small_book[price]["asks"] += qty
            except:
                small_book[price]["asks"] = 0

    #Asks
    async def write_asks():
        await asyncio.sleep(0.01)
        for price in small_book:
            coord = price_label0["text"] - price

            #Check coord is within window and that "asks" is a key in small_book
            if coord >= 0 and coord < window_price_levels-1\
                and "asks" in small_book[price]:
                    eval(alabel.format(coord))["text"] = small_book[price]["asks"]

    #Bids
    async def write_bids():
        await asyncio.sleep(0.01)
        for price in small_book:
            coord = price_label0["text"] - price

            #Check coord is within window and that "bids" is a key in small_book
            if coord >= 0 and coord < window_price_levels-1\
                and "bids" in small_book[price]:
                    eval(blabel.format(coord))["text"] = small_book[price]["bids"]

    async def orderbook():
        for i in iter(int, 1): #marginally faster than while True
            if subscribed_bool == True and dict_setup == True:
                await get_request()
                await write_asks()
                await write_bids()
            await asyncio.sleep(0.5)
            #t.sleep(0.5)

    blabel = "bid_label{0}"
    alabel = "ask_label{0}"
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(orderbook())


#CLASSES

class Toolbar(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, bg="gainsboro", height=30, padx=3, pady=4, bd=3)
        self.parent = master

        subbutton = tk.Button(
            command = connect,
            master = self,
            text = "Subscribe",
            width = 10,
        )

        unsubbutton = tk.Button(
            master = self,
            command = disconnect,
            text = "Disconnect",
            width = 10,
            padx = 3
        )

        recenter = tk.Button(
            master = self,
            command = refresh,
            text = "Recenter",
            width = 10,
            padx = 3
        )

        clean = tk.Button(
            master = self,
            command = clean_volume,
            text = "Clean",
            width = 10,
            padx = 3
        )

        subbutton.pack(side = "left")
        unsubbutton.pack(side = "left")
        recenter.pack(side="left")
        clean.pack(side="left")

class Tradetools(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, bg="silver", width = wwidth / 4)
        self.parent = master

        global trademodebutton
        global pnllabel
        global positionlabel
        global lotqty

        lotqty = tk.Label(
            master = self,
            text = f"Qty: {order_size}",
            height = 1,
        )

        ordersizeframe = tk.Frame(
            master = self,
            width = 80,
            height = 30,
            bg = "silver"
        )

        addlot = tk.Button(
            master = ordersizeframe,
            command = lambda: modqty("add"),
            text = add_lot_size,
            height = 1,
            width = 3
        )

        clearlot = tk.Button(
            master = ordersizeframe,
            command = lambda: modqty("clear"),
            text = "clear",
            height = 1,
            width = 5
        )

        trademodebutton = tk.Button(
            master = self,
            command = trade_mode_swap,
            text = "Trade mode",
            width = 10,
            relief = "flat",
            bg = "whitesmoke"
        )

        cancelallbutton = tk.Button(
            master = self,
            command = cancel_all,
            text = "Cancel all",
            width = 10,
            relief = "flat",
            bg = "whitesmoke"
        )

        positionlabel = tk.Label(
            master = self,
            text = "Position: ---",
            bg = "silver"
        )

        pnllabel = tk.Label(
            master = self,
            text = "PnL: ---",
            bg = "silver"
        )

        lotqty.pack(pady=5)
        addlot.pack(side="left", padx=1)
        clearlot.pack(side="left", padx=1)
        ordersizeframe.pack(side="top", padx=5, pady=5)
        ordersizeframe.pack_propagate(False)
        trademodebutton.pack(side="top", pady=5)
        cancelallbutton.pack(side="top", pady=5)
        positionlabel.pack(side="top")
        pnllabel.pack(side="top")

class Ordercolumn(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, bg="yellow", width = wwidth / 15)
        self.parent = master

        for i in range(window_price_levels):
            exec(f'''global order_frame{i}
global order_label{i}
order_frame{i} = tk.Frame(
            master = self,
            borderwidth = 1
        )
order_frame{i}.pack(fill="x")

order_label{i} = tk.Label(
            master=order_frame{i},
            text=None,
            font = font,
            anchor = "w",
            fg = "blue",
            bg = "gainsboro"
        )
order_label{i}.pack(fill="x")
order_label{i}.bind("<Button-1>", lambda e: place_order({i}, "BUY"))
order_label{i}.bind("<Button-2>", lambda e: cancel_order({i}))
order_label{i}.bind("<Button-3>", lambda e: place_order({i}, "SELL"))''')

class Priceaxis(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, bg="red", width = wwidth / 6)
        self.parent = master
        global highlight

        #arrange empty price ladder grid
        for i in range(window_price_levels):
            exec(f'''global price_frame{i}
global price_label{i}
price_frame{i} = tk.Frame(
                master = self,
                relief = tk.GROOVE,
                borderwidth = 1
            )
price_frame{i}.pack(fill="x")

price_label{i} = tk.Label(
                master = price_frame{i},
                text = "0",
                font = font,
                fg = "white",
                bg = "gray"
            )
price_label{i}.pack(fill="x")''')

class Volumecolumn(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, bg="green", width = wwidth / 6)
        self.parent = master

        for i in range(window_price_levels):
            exec(f'''global volume_frame{i}
global volume_label{i}
volume_frame{i} = tk.Frame(
            master = self,
            borderwidth = 1
        )
volume_frame{i}.pack(fill="x")

volume_label{i} = tk.Label(
            master = volume_frame{i},
            text=None,
            font = font,
            anchor = "w",
            bg = "gainsboro"
        )
volume_label{i}.pack(fill="x")''')

class Buycolumn(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, bg="blue", width = wwidth / 12)
        self.parent = master

        for i in range(window_price_levels):
            exec(f'''global buy_frame{i}
global buy_label{i}
buy_frame{i} = tk.Frame(
            master = self,
            borderwidth = 1
        )
buy_frame{i}.pack(fill="x")

buy_label{i} = tk.Label(
            master=buy_frame{i},
            text=None,
            font = font,
            anchor = "e",
            fg = "blue",
            bg = "gainsboro"
        )
buy_label{i}.pack(fill="x")''')

class Sellcolumn(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, bg="blue", width = wwidth / 12)
        self.parent = master

        for i in range(window_price_levels):
            exec(f'''global sell_frame{i}
global sell_label{i}
sell_frame{i} = tk.Frame(
            master = self,
            borderwidth = 1
        )
sell_frame{i}.pack(fill="x")

sell_label{i} = tk.Label(
            master=sell_frame{i},
            text=None,
            font = font,
            anchor = "w",
            fg = "maroon",
            bg = "gainsboro"
        )
sell_label{i}.pack(fill="x")''')

class Askcolumn(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, bg="orange", width = wwidth / 12)
        self.parent = master

        for i in range(window_price_levels):
            exec(f'''global ask_frame{i}
global ask_label{i}
ask_frame{i} = tk.Frame(
            master = self,
            borderwidth = 1,
            bg = "maroon"
        )
ask_frame{i}.pack(fill="x", side="top")

ask_label{i} = tk.Label(
            master = ask_frame{i},
            text = None,
            width = 0,
            font = font,
            fg = "white",
            bg = "maroon"
        )
ask_label{i}.pack(side="left")''')

class Bidcolumn(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, bg="pink", width = wwidth / 12)
        self.parent = master

        for i in range(window_price_levels):
            exec(f'''global bid_frame{i}
global bid_label{i}
bid_frame{i} = tk.Frame(
            master = self,
            borderwidth = 1,
            bg = "navy"
        )
bid_frame{i}.pack(fill="x", side="top")

#bid_bar{i} = tk.Frame(
#            master = bid_frame{i},
#            width = 0,
#            height = 17,
#            bg = "#468c57"
#        )
#bid_bar{i}.pack(side="left")

bid_label{i} = tk.Label(
            master = bid_frame{i},
            text = None,
            width = 0,
            font = font,
            fg = "white",
            bg = "navy"
        )
bid_label{i}.pack(side="right")''')

class MainApplication(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        tk.Frame.__init__(self, master, *args, **kwargs)
        self.parent = master

        #toolbars
        self.toolbar = Toolbar(self)
        self.toolbar.pack(side="top", fill="x")
        #Need to add:
            #Menu bar
            #Account info toolbar

        #columns
        self.tradetools = Tradetools(self)
        self.ordercolumn = Ordercolumn(self)
        self.priceaxis = Priceaxis(self)
        self.volumecolumn = Volumecolumn(self)
        self.buycolumn = Buycolumn(self)
        self.sellcolumn = Sellcolumn(self)
        self.bidcolumn = Bidcolumn(self)
        self.askcolumn = Askcolumn(self)

        #Trading toolbar
        self.tradetools.pack(side="left", fill="y")
        self.tradetools.pack_propagate(False)

        #Active orders
        self.ordercolumn.pack(side="left", fill="y")
        self.ordercolumn.pack_propagate(False)

        #Price levels
        self.priceaxis.pack(side="left", fill="y")
        self.priceaxis.pack_propagate(False)

        #Resting bids
        self.bidcolumn.pack(side="left", fill="y")
        self.bidcolumn.pack_propagate(False)

        #Sell volume
        self.sellcolumn.pack(side="left", fill="y")
        self.sellcolumn.pack_propagate(False)

        #Buy volume
        self.buycolumn.pack(side="left", fill="y")
        self.buycolumn.pack_propagate(False)

        #Resting asks
        self.askcolumn.pack(side="left", fill="y")
        self.askcolumn.pack_propagate(False)

        #Total volume
        self.volumecolumn.pack(side="left", fill="y")
        self.volumecolumn.pack_propagate(False)

    def update_title(self):
        global time
        global title_instrument_info
        time = datetime.now().strftime("%H:%M:%S.%f")[:-4]
        root.title("tori - " + title_instrument_info + " | " + time)
        root.after(100, self.update_title)


#MAIN

if __name__ == "__main__":
    listener_thread = threading.Thread(target=listener)
    orderbook_thread = threading.Thread(target=orderbook_listener)

    #Window setup
    root = tk.Tk()
    root.geometry(str(wwidth)+"x"+str(40 + (window_price_levels * 19)))
    root.attributes('-topmost', True)

    main = MainApplication(root)
    main.pack(side="top", fill="both", expand=True)

    main.update_title()

    print("\ntori\n\nReady to connect.")

    listener_thread.start()
    orderbook_thread.start()

    if auto_subscribe == True:
        connect()

    if init_trademode == True:
        print("! Starting in trade mode.")
        trade_mode_swap()

    root.mainloop()

    listener_thread.join()
    orderbook_thread.join()
