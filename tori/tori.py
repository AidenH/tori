import websockets
from datetime import datetime
import tkinter as tk

from binance_f import SubscriptionClient
from binance_f.constant.test import *
from binance_f.model import *
from binance_f.exception.binanceapiexception import BinanceApiException
from binance_f.base.printobject import *

import keys

#setup
instrument = "ethusdt"
wwidth = 400
wheight = 700
global_lastprice = 0

window = tk.Tk()
window.geometry(str(wwidth)+"x"+str(wheight))
window.attributes('-topmost', True)

sub_client = SubscriptionClient(api_key=keys.api, secret_key=keys.secret)

#funcs
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
        window.title(instrument + " " + time)
        global_lastprice = int(round(event.price, 0))

        curprice["text"] = str(global_lastprice) + " x " + str(event.qty)

        print(str(global_lastprice) + " " + str(datetime.now()))

    else:
        print("Unknown Data:")

    print()

def error(e: 'BinanceApiException'):
    print(e.error_code + e.error_message)

#classes
class priceaxis:
    def __init__():
        pass

#tkinter
curprice = tk.Label(
    text = "price x quantity"
)

subbutton = tk.Button(
    command = connect,
    text = "Subscribe",
    width = 10,
    height = 2
)

unsubbutton = tk.Button(
    command = disconnect,
    text = "Disconnect",
    width = 10,
    height = 2
)

price_axis_frame = tk.Frame(
    master = window,
    width = wwidth / 5,
    height = wheight,
    bg = "red",
)

#tkinter packs
price_axis_frame.pack(side = "left")

curprice.pack()
subbutton.pack()
unsubbutton.pack()

window.mainloop()
