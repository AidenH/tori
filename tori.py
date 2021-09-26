# tori
# Copyright (C) 2021  Aiden Holmans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
from datetime import datetime
import tkinter as tk
import threading
import asyncio
import time as t
import numpy as np

from binance_f import RequestClient
from binance_f import SubscriptionClient
from binance_f.constant.test import *
from binance_f.model import *
from binance_f.exception.binanceapiexception import BinanceApiException
from binance_f.base.printobject import *

from settings import *
import utils


# Root environment variables
root = tk.Tk()
wwidth = 370
wheight = 988
font = "arial 7 bold"
title_instrument_info = "none"

# Dom-related variables
dict_setup = False
ladder_midpoint = int(window_price_levels / 2) - 2  # Otherwise 23 if height 50
subscribed_bool = False
orderbook_subscribed_bool = False
global_lastprice = 0
prev_coord = 0
coord = 0
prices = {}
small_book = {0 : {"bids" : 0, "asks" : 0}}
last_trade = {"qty" : 0, "buyer" : False}
listener_safe = True

plabel = "price_label{0}"
vlabel = "volume_label{0}"
blabel = "buy_label{0}"
slabel = "sell_label{0}"
olabel = "order_label{0}"
bidlabel = "bid_label{0}"
asklabel = "ask_label{0}"

total_buy_volume = 0
total_sell_volume = 0

# Trading variables
trade_mode = False
flatten_mode = False
open_orders = {}
open_position = {"entry" : 0, "coord" : 0, "qty" : 0, "pnl": 0}

sub_client = SubscriptionClient(api_key=api_key, secret_key=secret_key)
request_client = RequestClient(api_key=api_key, secret_key=secret_key)

ladder_dict = {}
for i in range(window_price_levels):
    ladder_dict[i] = 0


# GLOBAL FUNCS

def connect():
    global dict_setup
    global subscribed_bool

    dict_setup = False

    # Connection results for unittest
    connect_result = {"agg_result": False, "data_result": False}

    if subscribed_bool == False:
        subscribed_bool = True

        # Subscribe to aggregate trade stream
        print("\nSubscribing... - " + time)

        try:
            sub_client.subscribe_aggregate_trade_event(instrument,
                handle_agg_trades_callback, error)
            connect_result["agg_result"] = True
        except:
            print(sys.exc_info())

        # Subscribe to user data
        print("Connecting to user data stream... - " + time)

        try:
            listenkey = request_client.start_user_data_stream()
            sub_client.subscribe_user_data_event(listenkey, handle_user_data_callback, error)
            connect_result["data_result"] = True
        except:
            print(sys.exc_info())

        keepalive()

        # return passes for unittest
        return connect_result

    else:
        print("Already running.")

def disconnect():
    global title_instrument_info
    global subscribed_bool

    title_instrument_info = "none"
    subscribed_bool = False
    orderbook_subscribed_bool = False
    disconnect_result = False

    try:
        sub_client.unsubscribe_all()
        print("\n\nDisconnected.\n")

        disconnect_result = True
    except:
        print(sys.exc_info())

    return disconnect_result

def keepalive():
    print("Pinging server...")

    try:
        request_client.keep_user_data_stream()
        print("Ping success.")
    except:
        print("Could not ping server.")

    root.after(3599999, keepalive)

# get aggregate trades data
def handle_agg_trades_callback(data_type: 'SubscribeMessageType', event: 'any'):
    global dict_setup, prices, global_lastprice, title_instrument_info, coord
    global last_trade, total_buy_volume, total_sell_volume

    coord = int(price_label0["text"]) - global_lastprice

    if data_type == SubscribeMessageType.RESPONSE:
        # Supressing event id printing for now due to console clutter.
        # print("EventID: ", event)
        pass

    elif data_type == SubscribeMessageType.PAYLOAD:
        # PrintBasic.print_obj(event)    # keep for full aggtrade payload example

        # set current global_lastprice
        # global_lastprice = int(round(event.price, 0))
        global_lastprice = utils.round(event.price)
        print(global_lastprice)

        # set local price variable
        local_lastprice = global_lastprice
        # update window title ticker info
        title_instrument_info = instrument + " " + str(local_lastprice)

        # Populate price levels dictionary
        if dict_setup == False:
            print("Set up dictionary - " + time + "\n")

            # tick_size other than 1 not yet working.
            # Subscriptionprocess error on start.
            for i in np.arange(0, local_lastprice + local_lastprice, tick_size):
                # Init price level volume data
                prices[i] = {"volume" : 0, "buy" : 0, "sell" : 0}

            # This and refresh() for us to have a midpoint coord on startup
            #    in order to avoid refresh() spamming because highlight_trade_price hasn't received
            #    a coord outside the auto-recenter trigger zones
            price_label0["text"] = global_lastprice+ladder_midpoint
            coord = int(price_label0["text"]) - global_lastprice

            dict_setup = True

            main.refresh()
            main.highlight_trade_price()

            main.volumecolumn.volume_column_populate(False)
            main.buycolumn.buy_column_populate(False)
            main.sellcolumn.sell_column_populate(False)

            init_check_user_status()

        # add event order quantity to price[volume] dict key
        prices[local_lastprice]["volume"] += round(event.qty, 0)
        last_trade["qty"] = int(round(event.qty, 0))

        if event.isBuyerMaker == False:
            # if buyer
            last_trade["buyer"] = True
            prices[local_lastprice]["buy"] += round(event.qty, 0)
            total_buy_volume += event.qty
        else:
            # if seller
            last_trade["buyer"] = False
            prices[local_lastprice]["sell"] += round(event.qty, 0)
            total_sell_volume += event.qty

        delta = int(total_buy_volume - total_sell_volume)
        deltainfolabel["text"] = f"Delta: {delta}"

    else:
        print("Unknown Data:")

# get user data for position updates, balance etc.
def handle_user_data_callback(data_type: 'SubscribeMessageType', event: 'any'):
    if data_type == SubscribeMessageType.RESPONSE:
        # Supressing event id printing for now due to console clutter.
        # print("EventID: ", event)
        pass

    elif data_type == SubscribeMessageType.PAYLOAD:

        '''print("\n--------------EVENT--------------")
        PrintBasic.print_obj(event)
        print("------------END EVENT------------")'''

        # If new order received, add to open_orders
        if event.eventType == "ORDER_TRADE_UPDATE" and event.orderStatus == "NEW":
            if event.price not in open_orders:
                open_orders[int(event.price)] = {}

            open_orders[event.price]["side"] = event.side

            if "ids" in open_orders[event.price]:
                open_orders[event.price]["ids"].append(event.orderId)
            else:
                open_orders[event.price]["ids"] = []
                open_orders[event.price]["ids"] = [event.orderId]

            if "qty" in open_orders[event.price]:
                open_orders[event.price]["qty"] += event.origQty
            else:
                open_orders[event.price]["qty"] = event.origQty

            print(f"Order {event.side} {event.origQty} at {int(event.price)} placed. - {time}\n")

            print(open_orders)

        # Check if open order has been filled and then remove from open_orders
        if (event.eventType == "ORDER_TRADE_UPDATE" and
            event.orderStatus == "FILLED" and event.type != "MARKET"):
            PrintBasic.print_obj(event)
            # Check for matching order id by event.price/open_orders[price]
            for id in list(open_orders[event.price]["ids"]):
                # If event id matches an open_orders id, then delete id from dict
                if id == event.orderId:
                    print(ladder_dict[0])
                    price = int(round(float(event.price), 0))
                    coord = ladder_dict[0] - price

                    # Remove id key & data from open orders price level
                    open_orders[event.price]["ids"].remove(id)

                    # If open_orders is empty of ids after this, remove that price level from dict
                    if open_orders[event.price]["ids"] == []:
                        print(f"empty - no orders at {event.price}")
                        open_orders.pop(event.price, None)
                        eval(olabel.format(coord))["text"] = ""

                    # Otherwise just subtract order qty from dict level qty
                    else:
                        print("id left, subbing from order qty")
                        open_orders[event.price]["qty"] -= event.origQty
                        eval(olabel.format(coord))["text"] -= event.origQty

            # Refresh in case of adding to position size,
            # we need to write a new, averaged entry price
            main.refresh()

        # If update is order cancel, remove order from open_orders and clean label
        if event.eventType == "ORDER_TRADE_UPDATE" and event.orderStatus == "CANCELED":
            price = int(event.price)
            coord = ladder_dict[0] - price

            open_orders[price]["ids"].remove(event.orderId)

            # If every id has been deleted at the price level, remove level from
            # open orders list
            # Consider adding try & except here.
            if open_orders[price]["ids"] == []:
                open_orders.pop(price, None)

            # Reset level label text if within window
            if coord >= 0 and coord <= window_price_levels-1:
                eval(olabel.format(coord))["text"] = ""

            print(f"\norders: {open_orders}")

        if event.eventType == "ACCOUNT_UPDATE":
            print("\n-----------POSITIONS-------------")

            for i in range(len(event.positions)):
                if event.positions and event.positions[i].symbol == instrument.upper():
                    # If account update event details open position, add to open_position
                    if event.positions[i].amount != 0:

                        PrintBasic.print_obj(event.positions[i])

                        open_position["entry"] = int(round(event.positions[i].entryPrice, 0))
                        open_position["qty"] = event.positions[i].amount
                        open_position["coord"] = int(price_label0["text"]) - open_position["entry"]
                        print(f"Position: {open_position}")

                    # If account update event details no open position, clear open_position
                    elif event.positions[i].amount == 0:
                        PrintBasic.print_obj(event.positions[i])
                        entry_coord = open_position["coord"]

                        exec(f"price_label{entry_coord}['text'] = '{ladder_dict[entry_coord]}'")
                        exec(f"price_label{entry_coord}['fg'] = 'white'")
                        exec(f"price_label{entry_coord}['bg'] = 'gray'")

                        open_position["entry"] = 0
                        open_position["coord"] = 0
                        open_position["qty"] = 0
                        print(f"{open_position}")
                        print(f"Position closed with PnL: {open_position['pnl']}")
                        open_position["pnl"] = 0

            print("---------END POSITIONS-----------\n")

    else:
        print("Unknown Data:")

def error(e: 'BinanceApiException'):
    print(e.error_code + e.error_message)

def init_check_user_status():
    global open_position
    global open_orders

    pos_result = request_client.get_position()
    ord_result = request_client.get_open_orders()

    # Check open position and add to open_position
    for i in range(len(pos_result)):
        if pos_result[i].symbol == instrument.upper() and pos_result[i].positionAmt != 0:
            entry = int(pos_result[i].entryPrice)

            open_position = {"entry": entry,
                "coord": ladder_dict[0] - entry,
                "qty": pos_result[i].positionAmt,
                "pnl": "%.2f" % pos_result[i].unrealizedProfit}

            print(f"\n! You have an open position on {instrument}:")
            print(f"{open_position['qty']} at {entry}")

    # Check open orders and add to open_orders
    for i in range(len(ord_result)):
        price = int(round(ord_result[i].price, 0))

        if price not in open_orders:
            open_orders[price] = {}

        open_orders[price]["side"] = ord_result[i].side

        if "ids" in open_orders[price]:
            open_orders[price]["ids"].append(ord_result[i].orderId)
        else:
            open_orders[price]["ids"] = []
            open_orders[price]["ids"] = [ord_result[i].orderId]

        if "qty" in open_orders[price]:
            open_orders[price]["qty"] += ord_result[i].origQty
        else:
            open_orders[price]["qty"] = ord_result[i].origQty

def term_program():
    print("Exiting tori...")
    os._exit(0)

def update_title():
    global time
    global title_instrument_info
    time = datetime.now().strftime("%H:%M:%S.%f")[:-4]
    root.title("tori - " + title_instrument_info + " | " + time)
    root.after(100, update_title)


# THREADS

def listener():
    # loop indefinitely with iter()
    for i in iter(int, 1):

        if subscribed_bool == True and dict_setup == True and listener_safe == True:

            # Handle open orders list and send to orders column
            for i in list(open_orders):
                coord = ladder_dict[0] - i

                # Check that coord is within window and price is in open_orders[]
                if coord >= 0 and coord <= window_price_levels-1 and i in open_orders:
                    # Order is buy
                    if open_orders[i]["side"] == "BUY":
                        eval(olabel.format(coord))["text"] = open_orders[i]["qty"]
                        eval(olabel.format(coord))["fg"] = "blue"

                    # Order is sell
                    elif open_orders[i]["side"] == "SELL":
                        eval(olabel.format(coord))["text"] = open_orders[i]["qty"]
                        eval(olabel.format(coord))["fg"] = "maroon"

            # LONG position PnL calculation
            if open_position["qty"] > 0:
                # calculate open long position pnl
                long_global = global_lastprice * open_position["qty"]
                long_position = open_position["entry"] * open_position["qty"]
                open_position["pnl"] = round(long_global - long_position, 3)

                # check whether pnl should be in point mode or cash mode
                if pnl_tick_mode == False:
                    pnllabel["text"] = "PnL: " + str(open_position["pnl"])
                else:
                    pnllabel["text"] = "PnL: " + str(global_lastprice - open_position["entry"]) + "tick"

                positionlabel["text"] = f"Position: {open_position['qty']}\n@{open_position['entry']}"

            # SHORT position PnL calculation
            elif open_position["qty"] < 0:
                # calculate open short position pnl
                short_global = global_lastprice * open_position["qty"]
                short_position = open_position["entry"] * open_position["qty"]
                open_position["pnl"] = round(short_global - short_position, 3)

                # check whether pnl should be in point mode or cash mode
                if pnl_tick_mode == False:
                    pnllabel["text"] = "PnL: " + str(open_position["pnl"])
                else:
                    pnllabel["text"] = "PnL: " + str(open_position["entry"] - global_lastprice) + "tick"

                positionlabel["text"] = f"Position: {open_position['qty']}"

            # NO POSITION pnl default
            else:
                positionlabel["text"] = "Position: ---"
                pnllabel["text"] = "PnL: ---"

        t.sleep(0.5)

def orderbook_listener():
    # Populate orderbook dictionary
    async def get_request():
        result = request_client.get_order_book(instrument, 500)

        await asyncio.sleep(0.01)

        # Reset orderbook labels
        for price in small_book:
            coord = ladder_dict[0] - price
            if coord >= 0 and coord < window_price_levels-1:
                eval(bidlabel.format(coord))["text"] = ""
                eval(asklabel.format(coord))["text"] = ""

        small_book.clear()

        # Add bids to small_book
        for i in result.bids:
            price = int(round(float(i.price), 0))
            qty = int(round(float(i.qty), 0))

            if price < (global_lastprice - book_size):
                break

            if price not in small_book:
                small_book[price] = {"bids": 0}

            try:
                small_book[price]["bids"] += qty
            except:
                small_book[price]["bids"] = 0

        # Add asks to small_book
        for i in result.asks:
            price = int(round(float(i.price), 0))
            qty = int(round(float(i.qty), 0))

            if price > (global_lastprice + book_size):
                break

            if price not in small_book:
                small_book[price] = {"asks": 0}

            try:
                small_book[price]["asks"] += qty
            except:
                small_book[price]["asks"] = 0

    # Asks
    async def write_asks():
        await asyncio.sleep(0.01)
        for price in small_book:
            coord = ladder_dict[0] - price

            # Check coord is within window and that "asks" is a key in small_book
            if coord >= 0 and coord < window_price_levels-1\
                and "asks" in small_book[price]:
                    eval(asklabel.format(coord))["text"] = small_book[price]["asks"]

    # Bids
    async def write_bids():
        await asyncio.sleep(0.01)
        for price in small_book:
            coord = ladder_dict[0] - price

            # Check coord is within window and that "bids" is a key in small_book
            if coord >= 0 and coord < window_price_levels-1\
                and "bids" in small_book[price]:
                    eval(bidlabel.format(coord))["text"] = small_book[price]["bids"]

    async def orderbook():
        for i in iter(int, 1): # Supposedly faster than "while True"
            if subscribed_bool == True and dict_setup == True:
                await get_request()
                await write_asks()
                await write_bids()
            await asyncio.sleep(0.5)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(orderbook())


# CLASSES

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
            command = lambda: main.refresh(),
            text = "Recenter",
            width = 10,
            padx = 3
        )

        clean = tk.Button(
            master = self,
            command = self.clean_volume,
            text = "Clean",
            width = 10,
            padx = 3
        )

        subbutton.pack(side = "left")
        unsubbutton.pack(side = "left")
        recenter.pack(side="left")
        clean.pack(side="left")

    def clean_volume(self):
        global total_buy_volume, total_sell_volume, delta

        for i in range(len(prices)):
            prices[i]["buy"] = prices[i]["sell"] = 0

        for i in range(window_price_levels):
            eval(blabel.format(i))["text"] = eval(slabel.format(i))["text"] = ""

        total_buy_volume = total_sell_volume = delta = 0

        print("clean volume - " + time)

class Tradetools(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, bg="silver", width = wwidth / 4)
        self.parent = master

        global trademodebutton
        global flattenlockbutton
        global pnllabel
        global positionlabel
        global lotqty
        global deltainfolabel

        lotqty = tk.Label(
            master = self,
            text = f"Qty: {lot_size}",
            height = 1,
        )

        # Order size frame
        ordersizeframe = tk.Frame(
            master = self,
            width = 80,
            height = 30,
            bg = "silver"
        )

        addlot = tk.Button(
            master = ordersizeframe,
            command = lambda: self.modqty("add"),
            text = lot_increment_size,
            height = 1,
            width = 3
        )

        clearlot = tk.Button(
            master = ordersizeframe,
            command = lambda: self.modqty("clear"),
            text = "clear",
            height = 1,
            width = 5
        )

        trademodebutton = tk.Button(
            master = self,
            command = self.trade_mode_swap,
            text = "Trade mode",
            width = 10,
            relief = "flat",
            bg = "whitesmoke"
        )

        # Flatten frame
        flattenbuttonframe = tk.Frame(
            master = self,
            bg = "silver"
        )

        flattenlockbutton = tk.Button(
            master = flattenbuttonframe,
            command = self.flatten_mode_swap,
            text = "L",
            relief = "flat",
            bg = "lightcoral"
        )

        flattenbutton = tk.Button(
            master = flattenbuttonframe,
            command = self.flatten,
            text = "Flatten",
            width = 7,
            relief = "flat",
            bg = "whitesmoke"
        )

        cancelallbutton = tk.Button(
            master = self,
            command = self.cancel_all,
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

        deltainfoframe = tk.Frame(
            master = self,
            height = 20,
            bg = "navy"
        )

        deltainfolabel = tk.Label(
            master = deltainfoframe,
            font = font,
            text = None,
            fg = "white",
            bg = "navy"
        )

        lotqty.pack(pady=5)
        addlot.pack(side="left", padx=1)
        clearlot.pack(side="left", padx=1)
        ordersizeframe.pack(side="top", padx=5, pady=5)
        ordersizeframe.pack_propagate(False)

        trademodebutton.pack(side="top", pady=5)

        flattenbuttonframe.pack(side="top", pady=5)
        flattenlockbutton.pack(side="left", padx=1)
        flattenbutton.pack(side="left")

        cancelallbutton.pack(side="top", pady=5)
        positionlabel.pack(side="top")
        pnllabel.pack(side="top")
        deltainfoframe.pack(side="bottom", fill="x")
        deltainfolabel.pack()

    def modqty(self, type):
        global lot_size

        if type == "add":
            lot_size += lot_increment_size
            lotqty["text"] = f"Qty: {'%.2f'%lot_size}"

        elif type == "clear":
            lot_size = 0
            lotqty["text"] = f"Qty: {'%.2f'%lot_size}"

    def flatten_mode_swap(self):
        global flatten_mode

        if not flatten_mode:
            flatten_mode = True
            flattenlockbutton["bg"] = "whitesmoke"
            print("\nFlatten lock deactivated.")

        else:
            flatten_mode = False
            flattenlockbutton["bg"] = "lightcoral"
            print("\nFlatten lock activated")

    def flatten(self):
        try:
            if flatten_mode:
                print(open_position)

                # if LONG
                if open_position["qty"] > 0:
                    request_client.post_order(symbol=instrument, side=OrderSide.SELL,
                        ordertype=OrderType.MARKET, quantity=abs(open_position["qty"]))
                    print("Long position flattened. - " + time)

                    self.cancel_all()

                # if SHORT
                elif open_position["qty"] < 0:
                    request_client.post_order(symbol=instrument, side=OrderSide.BUY,
                        ordertype=OrderType.MARKET, quantity=abs(open_position["qty"]))
                    print("Short position flattened. - " + time)

                    self.cancel_all()

                else:
                    print("No open positions recognized.")

        except Exception as e:
            print(f"! Error while flattening: {e}")

    def trade_mode_swap(self):
        global trade_mode

        if trade_mode == False:
            trade_mode = True
            trademodebutton["bg"] = "lightcoral"
            print("\nTrade mode activated.")

        else:
            trade_mode = False
            trademodebutton["bg"] = "whitesmoke"
            print("\nTrade mode disabled.")

    def cancel_all(self):
        try:
            request_client.cancel_all_orders(symbol=instrument)
            print("All orders cancelled. - " + time)
        except:
            print(f"! Error while cancelling all orders:\n{sys.exc_info()}")

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
            text=None,
            font = font,
            anchor = "w",
            fg = "blue",
            bg = "gainsboro"
        )
order_label{i}.pack(fill="x")
order_label{i}.bind("<Button-3>", lambda e: main.ordercolumn.cancel_order({i}))
''')

    def cancel_order(self, coord):
        if subscribed_bool == True and dict_setup == True and trade_mode == True:
            price = ladder_dict[coord]

            # For every order id at logged at a particular price level, cancel.
            try:
                for id in list(open_orders[price]["ids"]):
                    try:
                        result = request_client.cancel_order(symbol=instrument, orderId=id)
                    except Exception as err:
                        print(f"\n! Error cancelling order:\n{err.args}")
                        print("Check whether your order has already been cancelled.\n")
            except KeyError as k:
                print(f"\n! No orders found at price level {k}\n")

class Priceaxis(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, bg="red", width = wwidth / 6)
        self.parent = master
        global highlight

        # arrange empty price ladder grid
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
            master = volume_frame{i},
            text=None,
            font = font,
            anchor = "w",
            bg = "gainsboro"
        )
volume_label{i}.pack(fill="x")''')

    # volume cell update
    def volume_column_populate(self, clean):
        if dict_setup == True and coord >= 0 and coord < window_price_levels:
            eval(vlabel.format(coord))["text"] = str(prices[ladder_dict[coord]]["volume"])[:-2]

        if clean == False:
            root.after(100, self.volume_column_populate, False)

class Buycolumn(tk.Frame):
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
            text=None,
            font = font,
            anchor = "e",
            fg = "blue",
            bg = "gainsboro"
        )
buy_label{i}.pack(fill="x")''')

    def buy_column_populate(self, clean):
        if dict_setup == True and coord >= 0 and coord < window_price_levels:
            eval(blabel.format(coord))["text"] = str(prices[ladder_dict[coord]]["buy"])[:-2]

        if clean == False:
            root.after(100, self.buy_column_populate, False)

class Sellcolumn(tk.Frame):
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
            text=None,
            font = font,
            anchor = "w",
            fg = "maroon",
            bg = "gainsboro"
        )
sell_label{i}.pack(fill="x")''')

    def sell_column_populate(self, clean):
        if dict_setup == True and coord >= 0 and coord < window_price_levels:
            eval(slabel.format(coord))["text"] = str(prices[ladder_dict[coord]]["sell"])[:-2]

        if clean == False:
            root.after(100, self.sell_column_populate, False)

class Askcolumn(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, bg="orange", width = wwidth / 12)
        self.parent = master

        for i in range(window_price_levels):
            exec(f'''global ask_frame{i}
global ask_label{i}
ask_frame{i} = tk.Frame(
            master = self,
            borderwidth = 1,
            bg = "maroon"
        )
ask_frame{i}.pack(fill="x", side="top")

ask_label{i} = tk.Label(
            master = ask_frame{i},
            text = None,
            width = 5,
            font = font,
            fg = "white",
            bg = "maroon",
            anchor = "w"
        )
ask_label{i}.pack(side="left")
ask_label{i}.bind("<Button-1>", lambda e: main.askcolumn.place_order_sell({i}))''')

    def place_order_sell(self, coord):
        if subscribed_bool == True and dict_setup == True and trade_mode == True:
            price = ladder_dict[coord]

            # Send SHORT order to binance
            if lot_size > 0:
                # Limit
                if price > global_lastprice:
                    result = request_client.post_order(symbol=instrument, side=OrderSide.SELL,
                        ordertype=OrderType.LIMIT, price=price, quantity="%.2f"%lot_size,
                            timeInForce=TimeInForce.GTC,)
                    print(f"\nLimit order SELL {lot_size} at {price} sent to exchange. - {time}")

                # Stop limit
                else:
                    result = request_client.post_order(symbol=instrument, side=OrderSide.SELL,
                        ordertype=OrderType.STOP, price=price-1, stopPrice=price, quantity="%.2f"%lot_size,
                            timeInForce=TimeInForce.GTC,)
                    print(f"\nStop limit order SELL {lot_size} at {price} sent to exchange. - {time}")

            else:
                print(f"\n! Error: Order SELL {lot_size} at {price} was not sent.")
                print(f"Can't send zero lot order. - {time}")

class Bidcolumn(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, bg="pink", width = wwidth / 12)
        self.parent = master

        for i in range(window_price_levels):
            exec(f'''global bid_frame{i}
global bid_label{i}
bid_frame{i} = tk.Frame(
            master = self,
            borderwidth = 1,
            bg = "navy"
        )
bid_frame{i}.pack(fill="x", side="top")

#bid_bar{i} = tk.Frame(
#            master = bid_frame{i},
#            width = 0,
#            height = 17,
#            bg = "#468c57"
#        )
#bid_bar{i}.pack(side="left")

bid_label{i} = tk.Label(
            master = bid_frame{i},
            text = None,
            width = 5,
            font = font,
            fg = "white",
            bg = "navy",
            anchor = "e"
        )
bid_label{i}.pack(side="right")
bid_label{i}.bind("<Button-1>", lambda e: main.bidcolumn.place_order_buy({i}))''')

    def place_order_buy(self, coord):
        if subscribed_bool == True and dict_setup == True and trade_mode == True:
            price = ladder_dict[coord]

            # Send LONG order to binance
            if lot_size > 0:
                # Limit
                if price < global_lastprice:
                    result = request_client.post_order(symbol=instrument, side=OrderSide.BUY,
                        ordertype=OrderType.LIMIT, price=price, quantity="%.2f"%lot_size,
                            timeInForce=TimeInForce.GTC,)
                    print(f"\nLimit order BUY {lot_size} at {price} sent to exchange. - {time}")

                # Stop limit
                else:
                    result = request_client.post_order(symbol=instrument, side=OrderSide.BUY,
                        ordertype=OrderType.STOP, price=price+1, stopPrice=price, quantity="%.2f"%lot_size,
                            timeInForce=TimeInForce.GTC,)
                    print(f"\nStop limit order BUY {lot_size} at {price} sent to exchange. - {time}")

            else:
                print(f"\n! Error: Order BUY {lot_size} at {price} was not sent.")
                print(f"Can't send zero lot order. - {time}")

class MainApplication(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.parent = master

        # toolbars
        self.toolbar = Toolbar(self)
        self.toolbar.pack(side="top", fill="x")
        # Need to add:
            # Menu bar
            # Account info toolbar

        # columns
        self.tradetools = Tradetools(self)
        self.ordercolumn = Ordercolumn(self)
        self.priceaxis = Priceaxis(self)
        self.volumecolumn = Volumecolumn(self)
        self.buycolumn = Buycolumn(self)
        self.sellcolumn = Sellcolumn(self)
        self.bidcolumn = Bidcolumn(self)
        self.askcolumn = Askcolumn(self)

        # Trading toolbar
        self.tradetools.pack(side="left", fill="y")
        self.tradetools.pack_propagate(False)

        # Active orders
        self.ordercolumn.pack(side="left", fill="y")
        self.ordercolumn.pack_propagate(False)

        # Price levels
        self.priceaxis.pack(side="left", fill="y")
        self.priceaxis.pack_propagate(False)

        # Resting bids
        self.bidcolumn.pack(side="left", fill="y")
        self.bidcolumn.pack_propagate(False)

        # Sell volume
        self.sellcolumn.pack(side="left", fill="y")
        self.sellcolumn.pack_propagate(False)

        # Buy volume
        self.buycolumn.pack(side="left", fill="y")
        self.buycolumn.pack_propagate(False)

        # Resting asks
        self.askcolumn.pack(side="left", fill="y")
        self.askcolumn.pack_propagate(False)

        # Total volume
        self.volumecolumn.pack(side="left", fill="y")
        self.volumecolumn.pack_propagate(False)

    # Recenter everything based on last trade price
    def refresh(self):
        global ladder_dict

        # populate the ladder cell dictionary
        for i in range(window_price_levels):
            ladder_dict[i] = global_lastprice+ladder_midpoint-i

            eval(asklabel.format(i))["text"] = ""
            eval(bidlabel.format(i))["text"] = ""

            eval(olabel.format(i))["text"] = ""

            exec(f"price_label{i}['bg'] = 'gray'")
            exec(f"price_label{i}['fg'] = 'white'")

        # write dictionary values to frame
        for i in range(window_price_levels-1, -1, -1):
            eval(plabel.format(i))["text"] = ladder_dict[i]
            eval(vlabel.format(i))["text"] = str(prices[ladder_dict[i]]["volume"])[:-2]
            eval(blabel.format(i))["text"] = str(prices[ladder_dict[i]]["buy"])[:-2]
            eval(slabel.format(i))["text"] = str(prices[ladder_dict[i]]["sell"])[:-2]

        print("Refresh - " + time)

    def highlight_trade_price(self):
        global prev_coord

        if dict_setup == True and coord >= 0 and coord < window_price_levels:
            # If there is an open position, mark it at entry_coord location
            if open_position["qty"] != 0:
                # Entry coord = top of ladder/highest price - current position entry price
                entry_coord = ladder_dict[0] - open_position["entry"]

                e = open_position["entry"]
                q = open_position["qty"]

                # If entry is within frame, place styled highlight
                if entry_coord >= 0 and entry_coord <= (window_price_levels - 1):
                    if open_position["qty"] > 0:
                        exec(f"price_label{entry_coord}['bg'] = 'mediumpurple'")

                    elif open_position["qty"] < 0:
                        exec(f"price_label{entry_coord}['bg'] = 'firebrick'")

                    exec(f"price_label{entry_coord}['text'] = '{e} {q}'")

            # Need to be able to remove position marking dynamically as well!

            # Mark last trade qty and side on price axis
            if last_trade["qty"] > vol_filter:
                exec(f"price_label{coord}['text'] = last_trade['qty']")

                if last_trade["buyer"]:
                    exec(f"price_label{coord}['fg'] = 'lime'")
                else:
                    exec(f"price_label{coord}['fg'] = 'red'")

            # Highlight current trade price coord on axis
            exec(f"price_label{coord}['bg'] = 'blue'")
            exec(f"buy_label{coord}['bg'] = 'silver'")
            exec(f"sell_label{coord}['bg'] = 'silver'")

            # If new price from last coord, reset previous coord's label style
            if coord != prev_coord:
                exec(f"price_label{prev_coord}['text'] = ladder_dict[prev_coord]")

                exec(f"price_label{prev_coord}['bg'] = 'gray'")
                exec(f"price_label{prev_coord}['fg'] = 'white'")
                exec(f"buy_label{prev_coord}['bg'] = 'gainsboro'")
                exec(f"sell_label{prev_coord}['bg'] = 'gainsboro'")

            prev_coord = coord

        if dict_setup == True and (coord < 6 or coord > (window_price_levels-6)):
            refresh()

        root.after(100, self.highlight_trade_price)


# MAIN

if __name__ == "__main__":
    listener_thread = threading.Thread(target=listener)
    orderbook_thread = threading.Thread(target=orderbook_listener)

    # Window setup
    root.geometry(str(wwidth)+"x"+str(40 + (window_price_levels * 19)))
    root.attributes('-topmost', True)

    # Window can only be resized by setting window_price_levels in settings.py
    root.resizable(width=False, height=False)

    main = MainApplication(root)
    main.pack(side="top", fill="both", expand=True)

    update_title()

    print("\ntori\n\nReady to connect.")

    listener_thread.start()
    orderbook_thread.start()

    if auto_subscribe == True:
        print(f"! Auto-subscribing to {instrument}")
        connect()

    if init_trademode == True:
        print("! Starting in trade mode.")
        main.tradetools.trade_mode_swap()

    root.protocol("WM_DELETE_WINDOW", term_program)
    root.mainloop()
