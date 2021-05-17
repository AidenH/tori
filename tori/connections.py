from binance_f import SubscriptionClient
from binance_f.constant.test import *
from binance_f.model import *
from binance_f.exception.binanceapiexception import BinanceApiException
from binance_f.base.printobject import *

import keys

sub_client = SubscriptionClient(api_key=keys.api, secret_key=keys.secret)

def connect(instrument):
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
