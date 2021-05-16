import websockets
import tkinter as tk

from binance_f import SubscriptionClient
from binance_f.constant.test import *
from binance_f.model import *
from binance_f.exception.binanceapiexception import BinanceApiException
from binance_f.base.printobject import *

import keys

#setup
window = tk.Tk()
window.geometry("400x700")
window.attributes('-topmost', True)

sub_client = SubscriptionClient(api_key=keys.api, secret_key=keys.secret)

#funcs
def connect():
    print("test")
    sub_client.subscribe_aggregate_trade_event("btcusdt", callback, error)

def callback(data_type: 'SubscribeMessageType', event: 'any'):
    if data_type == SubscribeMessageType.RESPONSE:
        print("EventID: ", event)
    elif data_type == SubscribeMessageType.PAYLOAD:
        PrintBasic.print_obj(event)
        sub_client.unsubscribe_all()
    else:
        print("Unknown Data:")
    print()

def error(e: 'BinanceApiException'):
    print(e.error_code + e.error_message)

#tkinter
subbutton = tk.Button(
    command = connect,
    text = "Subscribe",
    width = 10,
    height = 2
)

subbutton.pack()

window.mainloop()
