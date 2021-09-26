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


# Tests at the moment remain unfinished. It's unclear whether the structure
# in which tori was initially written even allows for all tests to be added.
# It may require a full overhaul of the software to be able to implement testing
# where it counts, as there is too much tangling between functions currently.

import unittest
from unittest.mock import patch
import tkinter as tk

# import tori

from binance_f import RequestClient
from binance_f import SubscriptionClient

from settings import *
import utils

class Testtori(unittest.TestCase):

    # def test_connect(self):
    #     tori.time = "(test time)"
    #     connect_result = tori.connect()
    #     self.assertTrue(connect_result["agg_result"],
    #         "Problem subscribing to aggregate trade stream.")
    #     self.assertTrue(connect_result["data_result"],
    #         "Problem subscribing to user data stream.")

    # def test_disconnect(self):
    #     disconnect_result = tori.disconnect()
    #     self.assertTrue(disconnect_result)

    def test_round_half(self):
        price = 2990.62
        result = utils.round(price, tick_size)
        self.assertEqual(result, 2990.50)

if __name__ == "__main__":
    # root = tk.Tk()
    # main = tori.MainApplication(root)

    unittest.main()
