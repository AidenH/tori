import websockets
from datetime import datetime
import tkinter as tk

from binance_f import SubscriptionClient
from binance_f.constant.test import *
from binance_f.model import *
from binance_f.exception.binanceapiexception import BinanceApiException
from binance_f.base.printobject import *

import keys

#CONNECTIVITY
def connect():
    print("\nSubscribing...")
    sub_client.subscribe_aggregate_trade_event(instrument, callback, error)

def disconnect():
    print("\n\nDisconnected.\n")
    sub_client.unsubscribe_all()

def callback(data_type: 'SubscribeMessageType', event: 'any'):

    if data_type == SubscribeMessageType.RESPONSE:
        print("EventID: ", event)

    elif data_type == SubscribeMessageType.PAYLOAD:
        #PrintBasic.print_obj(event)    #keep for full aggtrade payload example
        time = datetime.now().strftime("%H:%M:%S.%f")
        root.title(instrument + " " + time)
        global_lastprice = int(round(event.price, 0))

        marketprice["text"] = str(global_lastprice) + " x " + str(event.qty)[:-2]

        print(str(global_lastprice) + " " + str(datetime.now()))

    else:
        print("Unknown Data:")

    print()

def error(e: 'BinanceApiException'):
    print(e.error_code + e.error_message)

#PRICE AXIS SETUP

def recenter():
    pass

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

        subbutton.pack(side = "left")
        unsubbutton.pack(side = "left")


class Priceaxis(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, bg="gray", width = wwidth / 6)
        self.parent = master
        global marketprice

        #price ladder grid
        for i in range(23):
            frame = tk.Frame(
                master = self,
                relief = tk.GROOVE,
                borderwidth = 1
            )
            frame.pack(fill="x")
            label = tk.Label(
                master=frame,
                text="text",
                font = font,
                bg="gray"
            )
            label.pack(fill="x")

        #market price
        marketprice = tk.Label(
            master = self,
            text = "Price",
            font = font,
            fg = "white",
            bg = "dimgrey"
        )
        marketprice.pack(fill="x")

        for i in range(24):
            frame = tk.Frame(
                master = self,
                relief = tk.GROOVE,
                borderwidth = 1
            )
            frame.pack(fill="x")
            label = tk.Label(
                master=frame,
                text="text",
                font = font,
                bg="gray"
            )
            label.pack(fill="x")

class MainApplication(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        tk.Frame.__init__(self, master, *args, **kwargs)
        self.parent = master
        self.toolbar = Toolbar(self)
        self.priceaxis = Priceaxis(self)

        self.toolbar.pack(side="top", fill="x")
        self.priceaxis.pack(side="left", fill="y")
        self.priceaxis.pack_propagate(False)

    def update_title(self):
        time = datetime.now().strftime("%H:%M:%S.%f")
        root.title(instrument + " " + time[:-4])
        root.after(100, self.update_title)

if __name__ == "__main__":
    instrument = "ethusdt"
    wwidth = 400
    wheight = 1000
    font = "arial 7"

    sub_client = SubscriptionClient(api_key=keys.api, secret_key=keys.secret)

    root = tk.Tk()
    root.geometry(str(wwidth)+"x"+str(wheight))
    root.attributes('-topmost', True)

    main = MainApplication(root)
    main.pack(side="top", fill="both", expand=True)

    print(marketprice["text"])
    main.update_title()

    root.mainloop()
