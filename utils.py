import math
from settings import tick_size

def round_price(num):
    decimal_places = str(tick_size).split(".")[1] # Get digits after decimal
    rounded = round(num, int(len(decimal_places)))

    return rounded