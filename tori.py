import requests
from datetime import datetime
import tkinter as tk
import multiprocessing
import threading
import time as t

from binance_f import RequestClient
from binance_f import SubscriptionClient
from binance_f.constant.test import *
from binance_f.model import *
from binance_f.exception.binanceapiexception import BinanceApiException
from binance_f.base.printobject import *

import keys

#FUNCTIONS

def connect():
    global dict_setup
    global subscribed_bool
    dict_setup = False

    if subscribed_bool == False:
        subscribed_bool = True
        print("\nSubscribing... - " + time)
        sub_client.subscribe_aggregate_trade_event(instrument, get_trades_callback, error)

        print("Connecting to user data stream... - " + time)
        listenkey = request_client.start_user_data_stream()
        sub_client.subscribe_user_data_event(listenkey, user_data_callback, error)
    else:
        print("Already running.")

    #Add keepalive?
    pass

def disconnect():
    global title_instrument_info
    global subscribed_bool
    title_instrument_info = "none"
    subscribed_bool = False

    print("\n\nDisconnected.\n")
    sub_client.unsubscribe_all()

    #get_orders_process.terminate()
    #orders_process_listener_thread.join()
    pass

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

        global_lastprice = int(round(event.price, 0))   #set current global_lastprice
        local_lastprice = global_lastprice #set local price variable
        title_instrument_info = instrument + " " + str(local_lastprice) #update window title ticker info

        #Populate price levels dictionary
        if dict_setup == False:
            print("Set up dictionary - " + time + "\n")

            for i in range(0, local_lastprice + local_lastprice):
                prices[i] = {"volume" : 0, "buy" : 0, "sell" : 0}   #only adding the total level volume information for the moment

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

        prices[local_lastprice]["volume"] += round(event.qty, 0)   #add event order quantity to price volume dict key
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
        print("\n--------------EVENT--------------")
        PrintBasic.print_obj(event)
        print("------------END EVENT------------")

        if event.eventType == "ORDER_TRADE_UPDATE" and event.orderStatus == "NEW":
            open_orders[event.orderId] = {"price" : event.price, "side" : event.side, "qty" : event.origQty}
            print(f"Order {event.side} {event.origQty} at {int(event.price)} placed.")

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
                    exec(f"price_label{entry_coord}['bg'] = 'coral'")

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

        print(f"Order {side} {order_size} at {price} sent to exchange.")

def cancel_order(coord):
    if subscribed_bool == True and dict_setup == True and trade_mode == True:
        price = ladder_dict[coord]
        label = "order_label{0}"
        print(price)

        for i in list(open_orders):
            if open_orders[i]["price"] == price:
                coord = int(price_label0["text"]) - int(open_orders[i]["price"])

                request_client.cancel_order(symbol=instrument, orderId=i)
                open_orders.pop(i, None)
                eval(label.format(coord))["text"] = ""

        print(f"after cancel: {open_orders}")

        #cancel all:
        #result = request_client.post_order(symbol=instrument, side=OrderSide.BUY,
            #ordertype=OrderType.LIMIT, price=price, quantity=order_size, timeInForce=TimeInForce.GTC,)

#Thread
def listener():
    global global_lastprice
    label = "order_label{0}"

    if subscribed_bool == True and dict_setup == True:
        print(open_orders)
        for i in open_orders:
            coord = int(price_label0["text"]) - int(open_orders[i]["price"])

            if coord >= 0 and coord <= 49:

                #If order is buy
                if open_orders[i]["side"] == "BUY":
                    pass
                    eval(label.format(coord))["text"] = str(open_orders[i]["qty"])
                    eval(label.format(coord))["fg"] = "blue"

                if open_orders[i]["side"] == "SELL":
                    eval(label.format(coord))["text"] = str(open_orders[i]["qty"])
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
            command = trade_mode_swap,
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
            text="",
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
        global window_price_levels
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
    global window_price_levels

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
            master=volume_frame{i},
            text="",
            font = font,
            anchor = "w",
            bg = "gainsboro"
        )
volume_label{i}.pack(fill="x")''')

class Buycolumn(tk.Frame):
    global window_price_levels

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
            text="",
            font = font,
            anchor = "w",
            fg = "blue",
            bg = "gainsboro"
        )
buy_label{i}.pack(fill="x")''')

class Sellcolumn(tk.Frame):
    global window_price_levels

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
            text="",
            font = font,
            anchor = "w",
            fg = "maroon",
            bg = "gainsboro"
        )
sell_label{i}.pack(fill="x")''')

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
            #Order/position parameters and info

        #columns
        self.tradetools = Tradetools(self)
        self.ordercolumn = Ordercolumn(self)
        self.priceaxis = Priceaxis(self)
        self.volumecolumn = Volumecolumn(self)
        self.buycolumn = Buycolumn(self)
        self.sellcolumn = Sellcolumn(self)

        self.tradetools.pack(side="left", fill="y")
        self.tradetools.pack_propagate(False)

        self.ordercolumn.pack(side="left", fill="y")
        self.ordercolumn.pack_propagate(False)

        self.priceaxis.pack(side="left", fill="y")
        self.priceaxis.pack_propagate(False)

        self.sellcolumn.pack(side="left", fill="y")
        self.sellcolumn.pack_propagate(False)

        self.buycolumn.pack(side="left", fill="y")
        self.buycolumn.pack_propagate(False)

        self.volumecolumn.pack(side="left", fill="y")
        self.volumecolumn.pack_propagate(False)

    def update_title(self):
        global time
        global title_instrument_info
        time = datetime.now().strftime("%H:%M:%S.%f")[:-4]
        root.title("tori - " + title_instrument_info + " " + time)
        root.after(100, self.update_title)

#MAIN

if __name__ == "__main__":

    #Root environment variables
    instrument = "ethusdt"
    wwidth = 400
    wheight = 988
    font = "arial 7 bold"
    window_price_levels = 50    #need to generate this dynamically based on the window size at some point
    title_instrument_info = "none"

    #Dom-related variables
    vol_filter = 5
    dict_setup = False
    ladder_midpoint = 23
    subscribed_bool = False
    global_lastprice = 0
    prev_coord = 0
    prices = {}
    coord = 0
    last_trade = {"qty" : 0, "buyer" : False}

    #Trading variables
    trade_mode = False
    pnl_point_mode = True
    precision = 2
    order_size = 0.01
    open_orders = {}
    open_position = {"entry" : 0, "coord" : 0, "qty" : 0, "pnl": 0}

    ladder_dict = {}
    for i in range(window_price_levels):
        ladder_dict[i] = 0

    sub_client = SubscriptionClient(api_key=keys.api, secret_key=keys.secret)
    request_client = RequestClient(api_key=keys.api, secret_key=keys.secret)

    listener_thread = threading.Thread(target=listener)

    #Window setup
    root = tk.Tk()
    #root.geometry(str(wwidth)+"x"+str(wheight))
    root.geometry(str(wwidth)+"x"+str(40 + (window_price_levels * 19)))
    root.attributes('-topmost', True)

    main = MainApplication(root)
    main.pack(side="top", fill="both", expand=True)

    main.update_title()

    print("\ntori\n\nReady to connect.")

    #highlight_trade_price()
    listener_thread.start()

    root.mainloop()

    listener_thread.join()
