import math

def round(num, tick_size):
    decimal_places = str(tick_size).split(".")[1] # Get digits after decimal
    multiplier = 10 ** len(decimal_places) # Multiplier to de-float number

    return tick_size