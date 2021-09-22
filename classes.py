from tori import *

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