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
        #marketprice["text"] = str(global_lastprice) + " x " + str(event.qty)[:-2]   #DEPRECATED set marketprice label to last price

        global_lastprice = int(round(event.price, 0))   #set current global_lastprice
        local_lastprice = global_lastprice #set local price variable
        title_instrument_info = instrument + " " + str(local_lastprice) #update window title ticker info
        print(str(local_lastprice) + " " + str(event.time))   #log price & time to console

        #Populate price levels dictionary
        if dict_setup == False:
            print("Set up dictionary.")
            for i in range(0, local_lastprice + local_lastprice):
                prices[i] = {"volume": 0}   #only adding the total level volume information for the moment
            dict_setup = True
            recenter_axis()
            #main.priceaxis.highlight_trade_price(local_lastprice)

        prices[local_lastprice]["volume"] += round(event.qty, 0)   #add event order quantity to price volume dict key
        print("cum. qty.: " + str(int(prices[local_lastprice]["volume"])))

        #recenter_axis()
        #volume_column_populate()
        #highlight_trade_price(local_lastprice)

    else:
        print("Unknown Data:")

    print()

def error(e: 'BinanceApiException'):
    print(e.error_code + e.error_message)

#recenter/price populate price axis
def rewrite_axis():
    global ladder_midpoint
    global global_lastprice
    global ladder_dict

    label = "price_label{0}"

    #populate the ladder cell dictionary
    for i in range(window_price_levels):
        ladder_dict[i] = global_lastprice-ladder_midpoint+i
    print(ladder_dict)

    #write dictionary values to frame
    for i in range(window_price_levels):
        eval(label.format(i))["text"] = ladder_dict[i]

    #OLD, bad performance
    '''for i in range(window_price_levels):
        global_lastprice["coordinate"] = ladder_midpoint
        exec(f"price_label{i}['text'] = str((global_lastprice['price']-ladder_midpoint)+{i})")
        #each label is referenced around the 23th (middle) row price level'''

#recursive volume cell update
def volume_column_populate():
    global subscribed_bool
    for i in range(window_price_levels):
        exec(f"volume_label{i}['text'] = str(int(prices[global_lastprice-ladder_midpoint+{i}]['volume']))")
        #needs to only recenter when price axis recenters!
    if subscribed_bool == True:
        root.after(100, volume_column_populate())

def highlight_trade_price():
    global global_lastprice

    highlight["text"] = global_lastprice
    root.after(100, highlight_trade_price)

def clean_volume():
    for i in range(len(prices)):
        prices[i]["volume"] = 0

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
            command = recenter_axis,
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
    global window_price_levels

    def __init__(self, master):
        tk.Frame.__init__(self, master, bg="red", width = wwidth / 6)
        self.parent = master
        global marketprice
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
                master=price_frame{i},
                text="0",
                font = font,
                bg="gray"
            )
price_label{i}.pack(fill="x")''')

        highlight = tk.Label(
            master = price_frame23,
            text = "0",
            font = font,
            fg = "white",
            bg = "blue",
        )
        highlight.place(y=-1, relwidth=1)

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
            bg="gainsboro"
        )
volume_label{i}.pack(fill="x")''')

class MainApplication(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        tk.Frame.__init__(self, master, *args, **kwargs)

        self.parent = master
        self.toolbar = Toolbar(self)
        self.priceaxis = Priceaxis(self)
        self.volumecolumn = Volumecolumn(self)

        self.toolbar.pack(side="top", fill="x")

        self.priceaxis.pack(side="left", fill="y")
        self.priceaxis.pack_propagate(False)

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
    volume_column_populate()

    root.mainloop()
