import tori

def connect():
    global dict_setup
    dict_setup = False

    print("\nSubscribing...")
    tori.sub_client.subscribe_aggregate_trade_event(instrument, callback, error)

def disconnect():
    print("\n\nDisconnected.\n")
    sub_client.unsubscribe_all()

def callback(data_type: 'SubscribeMessageType', event: 'any'):
    global dict_setup
    global prices
    global global_lastprice

    if data_type == SubscribeMessageType.RESPONSE:
        print("EventID: ", event)

    elif data_type == SubscribeMessageType.PAYLOAD:
        #PrintBasic.print_obj(event)    #keep for full aggtrade payload example

        global_lastprice = int(round(event.price, 0))   #set current global_lastprice

        marketprice["text"] = str(global_lastprice) + " x " + str(event.qty)[:-2]   #set marketprice label to last price

        print(str(global_lastprice) + " " + time)   #log price & time to console

        #Populate price levels dictionary
        if dict_setup == False:
            print("connect")
            for i in range(0, global_lastprice + global_lastprice):
                prices[i] = {"volume": 0}   #only adding the total level volume information for the moment
            dict_setup = True

            main.priceaxis.populate_ladder()

        prices[global_lastprice]["volume"] += round(event.qty, 3)   #add quantity to price volume key

        for i in range(global_lastprice-23, global_lastprice+24):
            print(str(i) + ": " + str(prices[i]))   #it's working!!

    else:
        print("Unknown Data:")

    print()

def error(e: 'BinanceApiException'):
    print(e.error_code + e.error_message)

def recenter():
    pass
