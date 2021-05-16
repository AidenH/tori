import websockets
import tkinter as tk
import binance_f

window = tk.Tk()
window.geometry("400x700")
window.attributes('-topmost', True)

def connect():
    print("test")

subbutton = tk.Button(
    command = connect,
    text = "Subscribe",
    width = 10,
    height = 2
)

subbutton.pack()

window.mainloop()
