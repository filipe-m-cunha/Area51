import argparse
import numpy as np
import pandas as pd
from datamodel import OrderDepth, TradingState, Order

#! change this import to get the newest Trader
from momentum_silding_window import Trader

# should amount to implementing the Wiki:
# https://imc-prosperity.notion.site/Writing-an-Algorithm-in-Python-c44b46f32941430fa1eccb6ff054be26

# our trader
trader = Trader()

# simulate for one day with 10000 timesteps
for i in range(0, 1e6, 100):
    # TODO
    state = TradingState(i, listings, order_depths, own_trades, market_trades, position, observations)
    order_list = trader.run(state)
    # TODO