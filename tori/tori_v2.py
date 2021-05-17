import websockets
from datetime import datetime
import tkinter as tk

from binance_f import SubscriptionClient
from binance_f.constant.test import *
from binance_f.model import *
from binance_f.exception.binanceapiexception import BinanceApiException
from binance_f.base.printobject import *

import keys

class MainApplication(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        tk.Frame.__init__(self, master, *args, **kwargs)
        self.parent = master

    def update_title(self):
        time = datetime.now().strftime("%H:%M:%S.%f")
        root.title(instrument + " " + time)
        root.after(100, self.update_title)

if __name__ == "__main__":
    instrument = "ethusdt"
    wwidth = 400
    wheight = 700

    root = tk.Tk()
    root.geometry(str(wwidth)+"x"+str(wheight))
    root.attributes('-topmost', True)

    main = MainApplication(root)
    main.pack(side="top", fill="both", expand=True)

    main.update_title()

    root.mainloop()
