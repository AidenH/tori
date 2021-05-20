import websockets
from datetime import datetime
import tkinter as tk

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

    print("\nSubscribing...")
    sub_client.subscribe_aggregate_trade_event(instrument, callback, error)

def disconnect():
    global title_instrument_info
    global subscribed_bool
    title_instrument_info = "none"
    subscribed_bool = False

    print("\n\nDisconnected.\n")
    sub_client.unsubscribe_all()

#main subscription functionality
def callback(data_type: 'SubscribeMessageType', event: 'any'):
    global dict_setup
    global prices
    global global_lastprice
    global title_instrument_info

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
            print("Set up dictionary - " + time)
            for i in range(0, local_lastprice + local_lastprice):
                prices[i] = {"volume" : 0, "buy" : 0}   #only adding the total level volume information for the moment
            dict_setup = True
            write_axis()
            volume_column_populate(False)
            buy_column_populate(False)
            #main.priceaxis.highlight_trade_price(local_lastprice)

        prices[local_lastprice]["volume"] += round(event.qty, 0)   #add event order quantity to price volume dict key

        if event.isBuyerMaker == False:
            prices[local_lastprice]["buy"] += round(event.qty, 0)

        #print("cum. qty.: " + str(int(prices[local_lastprice]["volume"])))

    else:
        print("Unknown Data:")

def error(e: 'BinanceApiException'):
    print(e.error_code + e.error_message)

#recenter/price populate price axis
def write_axis():
    global ladder_midpoint
    global global_lastprice
    global ladder_dict

    label = "price_label{0}"

    #populate the ladder cell dictionary
    for i in range(window_price_levels):
        ladder_dict[i] = global_lastprice+ladder_midpoint-i

    #write dictionary values to frame
    for i in range(window_price_levels, 0, -1):
        eval(label.format(i-1))["text"] = ladder_dict[i-1]

    print("Recenter - " + time)

    volume_column_populate(True)

    #OLD, bad performance
    '''for i in range(window_price_levels):
        global_lastprice["coordinate"] = ladder_midpoint
        exec(f"price_label{i}['text'] = str((global_lastprice['price']-ladder_midpoint)+{i})")
        #each label is referenced around the 23th (middle) row price level'''

#volume cell update
def volume_column_populate(clean):
    global subscribed_bool
    global global_lastprice
    global ladder_dict

    label = "volume_label{0}"

    for i in range(0, window_price_levels):
        if subscribed_bool == True:
            #print(str(prices[ladder_dict[i]]["volume"]))
            eval(label.format(i))["text"] = str(prices[ladder_dict[i]]["volume"])[:-2]

        #OLD, poor performance
        #exec(f"volume_label{i}['text'] = str(int(prices[global_lastprice-ladder_midpoint+{i}]['volume']))")
        #needs to only recenter when price axis recenters!

    if clean == False:
        root.after(100, volume_column_populate, False)

def buy_column_populate(clean):
    global subscribed_bool
    global global_lastprice
    global ladder_dict

    label = "buy_label{0}"

    for i in range(0, window_price_levels):
        if subscribed_bool == True:
            #print(str(prices[ladder_dict[i]]["volume"]))
            eval(label.format(i))["text"] = str(prices[ladder_dict[i]]["buy"])[:-2]

        #OLD, poor performance
        #exec(f"volume_label{i}['text'] = str(int(prices[global_lastprice-ladder_midpoint+{i}]['volume']))")
        #needs to only recenter when price axis recenters!

    if clean == False:
        root.after(100, buy_column_populate, False)

def highlight_trade_price():
    global global_lastprice
    global prev_highlight_price
    coord = int(price_label0["text"]) - global_lastprice #-24
    #label = 'price_label{0}["{1}"] = "blue"'

    #highlight["text"] = global_lastprice
    #highlight["master"] = price_frame2     #this would be ideal
    exec(f"price_label{coord}['bg'] = 'blue'")

    if global_lastprice != prev_highlight_price:
        for i in range(window_price_levels):
            exec(f"price_label{i}['bg'] = 'gray'")

    prev_highlight_price = global_lastprice

    if dict_setup == True and (coord < 10 or coord > 40):
        write_axis()

    root.after(200, highlight_trade_price)

def clean_volume():
    for i in range(len(prices)):
        prices[i]["volume"] = 0
    print("clean_volume() - " + time)

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
            command = write_axis,
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

        '''highlight = tk.Label(
            master = price_frame23,
            text = "0",
            font = font,
            fg = "white",
            bg = "blue",
        )
        highlight.place(y=-1, relwidth=1)'''

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
            text="0",
            font = font,
            anchor = "w",
            bg = "gainsboro"
        )
volume_label{i}.pack(fill="x")''')

class Buycolumn(tk.Frame):
    global window_price_levels

    def __init__(self, master):
        tk.Frame.__init__(self, master, bg="blue", width = wwidth / 6)
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
            text="0",
            font = font,
            anchor = "w",
            fg = "blue",
            bg = "gainsboro"
        )
buy_label{i}.pack(fill="x")''')

class MainApplication(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        tk.Frame.__init__(self, master, *args, **kwargs)

        self.parent = master
        self.toolbar = Toolbar(self)
        self.priceaxis = Priceaxis(self)
        self.volumecolumn = Volumecolumn(self)
        self.buycolumn = Buycolumn(self)

        self.toolbar.pack(side="top", fill="x")

        self.priceaxis.pack(side="left", fill="y")
        self.priceaxis.pack_propagate(False)
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

    #root env variables
    instrument = "ethusdt"
    wwidth = 400
    wheight = 988
    font = "arial 7 bold"
    window_price_levels = 50
    #^^need to generate this dynamically based on the window size at some point
    title_instrument_info = "none"

    #Dom-related variables
    dict_setup = False
    ladder_midpoint = 23
    subscribed_bool = False
    global_lastprice = 0
    prev_highlight_price = 0
    prices = {}

    ladder_dict = {}
    for i in range(window_price_levels):
        ladder_dict[i] = 0

    sub_client = SubscriptionClient(api_key=keys.api, secret_key=keys.secret)

    root = tk.Tk()
    root.geometry(str(wwidth)+"x"+str(wheight))
    root.attributes('-topmost', True)

    main = MainApplication(root)
    main.pack(side="top", fill="both", expand=True)

    main.update_title()

    highlight_trade_price()

    root.mainloop()
