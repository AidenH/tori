import websockets
import tkinter as tk

from binance_f import SubscriptionClient
from binance_f.constant.test import *
from binance_f.model import *
from binance_f.exception.binanceapiexception import BinanceApiException
from binance_f.base.printobject import *

import keys

#setup
instrument = "ethusdt"

window = tk.Tk()
window.geometry("400x700")
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
        lastprice["text"] = int(round(event.price, 0))
        print(int(round(event.price, 0)))
        #PrintBasic.print_obj(event)    #keep for full aggtrade payload example
    else:
        print("Unknown Data:")
    print()

def error(e: 'BinanceApiException'):
    print(e.error_code + e.error_message)

#classes
class priceaxis:

    pass

#tkinter
lastprice = tk.Label(
    text = "price"
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

lastprice.pack()
subbutton.pack()
unsubbutton.pack()

window.mainloop()
