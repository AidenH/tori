import websockets
from datetime import datetime
import tkinter as tk
import multiprocessing
import threading
import time

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
    subscribed_bool = True

    print("\nSubscribing... - " + time)
    sub_client.subscribe_aggregate_trade_event(instrument, get_trades_callback, error)

    print("Connecting to user data... - " + time)
    #sub_client.subscribe_aggregate_trade_event(instrument, user_data_callback, error)

def disconnect():
    global title_instrument_info
    global subscribed_bool
    title_instrument_info = "none"
    subscribed_bool = False

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

        global_lastprice = int(round(event.price, 0))   #set current global_lastprice
        local_lastprice = global_lastprice #set local price variable
        title_instrument_info = instrument + " " + str(local_lastprice) #update window title ticker info
        #print(str(local_lastprice) + " " + str(event.time))   #log price & time to console

        #Populate price levels dictionary
        if dict_setup == False:
            dict_setup = True
            print("Set up dictionary - " + time + "\n")

            for i in range(0, local_lastprice + local_lastprice):
                prices[i] = {"volume" : 0, "buy" : 0, "sell" : 0, "order" : {"side" : "", "qty" : 0}}   #only adding the total level volume information for the moment

            highlight_trade_price()
            volume_column_populate(False)
            buy_column_populate(False)
            sell_column_populate(False)

            get_orders_process.start()
            orders_process_listener_thread.start()
            #main.priceaxis.highlight_trade_price(local_lastprice)

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

        #print("cum. qty.: " + str(int(prices[local_lastprice]["volume"])))

    else:
        print("Unknown Data:")

def user_data_callback(data_type: 'SubscribeMessageType', event: 'any'):
    #grab user data here
    pass

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
        if prices[ladder_dict[i]]["order"]['qty'] > 0:
            eval(olabel.format(i))["text"] = str(f"%.{precision}f" % prices[ladder_dict[i]]["order"]["qty"])
        else:
            eval(olabel.format(i))["text"] = ""

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

        #OLD, poor performance
        #exec(f"volume_label{i}['text'] = str(int(prices[global_lastprice-ladder_midpoint+{i}]['volume']))")
        #needs to only recenter when price axis recenters!

    if clean == False:
        root.after(100, volume_column_populate, False)

def buy_column_populate(clean):
    global subscribed_bool
    global global_lastprice
    global ladder_dict
    global coord

    label = "buy_label{0}"

    eval(label.format(coord))["text"] = str(prices[ladder_dict[coord]]["buy"])[:-2]

    '''for i in range(0, window_price_levels):
        if subscribed_bool == True:
            #print(str(prices[ladder_dict[i]]["volume"]))
            eval(label.format(i))["text"] = str(prices[ladder_dict[i]]["buy"])[:-2]'''

        #OLD, poor performance
        #exec(f"volume_label{i}['text'] = str(int(prices[global_lastprice-ladder_midpoint+{i}]['volume']))")
        #needs to only recenter when price axis recenters!

    if clean == False:
        root.after(100, buy_column_populate, False)

def sell_column_populate(clean):
    global subscribed_bool
    global global_lastprice
    global ladder_dict
    global coord

    label = "sell_label{0}"

    eval(label.format(coord))["text"] = str(prices[ladder_dict[coord]]["sell"])[:-2]

    '''for i in range(0, window_price_levels):
        if subscribed_bool == True:
            #print(str(prices[ladder_dict[i]]["volume"]))
            eval(label.format(i))["text"] = str(prices[ladder_dict[i]]["sell"])[:-2]
        '''

        #OLD, poor performance
        #exec(f"volume_label{i}['text'] = str(int(prices[global_lastprice-ladder_midpoint+{i}]['volume']))")
        #needs to only recenter when price axis recenters!

    if clean == False:
        root.after(100, sell_column_populate, False)

def highlight_trade_price():
    global global_lastprice
    global prev_highlight_price
    global coord
    global prev_coord
    global last_trade
    #coord = int(price_label0["text"]) - global_lastprice
    #label = 'price_label{0}["{1}"] = "blue"'

    #highlight["text"] = global_lastprice
    #highlight["master"] = price_frame2     #this would be ideal
    if dict_setup == True:
        if last_trade["qty"] > vol_filter:
            exec(f"price_label{coord}['text'] = last_trade['qty']")

            if last_trade["buyer"]:
                exec(f"price_label{coord}['fg'] = 'lime'")
            else:
                exec(f"price_label{coord}['fg'] = 'red'")

        exec(f"price_label{coord}['bg'] = 'blue'")
        exec(f"buy_label{coord}['bg'] = 'silver'")
        exec(f"sell_label{coord}['bg'] = 'silver'")

        if coord != prev_coord:
            #for i in range(window_price_levels):
            exec(f"price_label{prev_coord}['text'] = ladder_dict[prev_coord]")

            exec(f"price_label{prev_coord}['bg'] = 'gray'")
            exec(f"price_label{prev_coord}['fg'] = 'white'")
            exec(f"buy_label{prev_coord}['bg'] = 'gainsboro'")
            exec(f"sell_label{prev_coord}['bg'] = 'gainsboro'")

    prev_coord = coord

    if dict_setup == True and (coord < 5 or coord > (window_price_levels-5)):
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

def place_order(coord):
    if subscribed_bool == True and dict_setup == True:
        price = ladder_dict[coord]

        prices[price]["order"]['qty'] += round(order_size, 2)
        exec(f"order_label{coord}['text'] = '%.{precision}f' % prices[{price}]['order']['qty']")
        print(f"Order {prices[price]['order']['qty']} placed at {price}")

        #refresh order column here
        pass

def get_orders(q, instrument, request_client):
    while 1 != 0:
        open_orders = request_client.get_open_orders(symbol=instrument)
        for i in range(len(open_orders)):
            print(open_orders[i].side, int(round(open_orders[i].price, 0)), open_orders[i].origQty)
            q.put([open_orders[i].side, int(round(open_orders[i].price, 0)), open_orders[i].origQty])
        time.sleep(0.2)

def orders_process_listener():
    #This is causing BIG freeze!
    a = queue.get()
    print(a)
    root.after(200, orders_process_listener)

#CLASSES

class Toolbar(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, bg="gainsboro", height=30, padx=3, pady=3, bd=3)
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

class Ordercolumn(tk.Frame):
    global window_price_levels

    def __init__(self, master):
        tk.Frame.__init__(self, master, bg="yellow", width = wwidth / 20)
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
order_label{i}.bind("<Button-1>", lambda e: place_order({i}))''')

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

        #columns
        self.ordercolumn = Ordercolumn(self)
        self.priceaxis = Priceaxis(self)
        self.volumecolumn = Volumecolumn(self)
        self.buycolumn = Buycolumn(self)
        self.sellcolumn = Sellcolumn(self)

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

    #trading variables
    precision = 1
    order_size = 0.1
    open_orders = None

    ladder_dict = {}
    for i in range(window_price_levels):
        ladder_dict[i] = 0

    sub_client = SubscriptionClient(api_key=keys.api, secret_key=keys.secret)
    request_client = RequestClient(api_key=keys.api, secret_key=keys.secret)

    queue = multiprocessing.Queue()

    get_orders_process = multiprocessing.Process(target=get_orders, args=(queue, instrument, request_client,))
    orders_process_listener_thread = threading.Thread(target=orders_process_listener)

    #Window setup
    root = tk.Tk()
    root.geometry(str(wwidth)+"x"+str(wheight))
    root.attributes('-topmost', True)

    main = MainApplication(root)
    main.pack(side="top", fill="both", expand=True)

    main.update_title()

    highlight_trade_price()

    root.mainloop()

    orders_process_listener_thread.join()
