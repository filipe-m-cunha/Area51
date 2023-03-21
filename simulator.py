import argparse
import numpy as np
import pandas as pd
from datamodel import OrderDepth, TradingState, Order, Listing, Trade
from typing import Dict, List

#! change this import to get the newest Trader
from momentum_silding_window import Trader

# should amount to implementing the Wiki:
# https://imc-prosperity.notion.site/Writing-an-Algorithm-in-Python-c44b46f32941430fa1eccb6ff054be26

# our trader
trader = Trader()

INPUT_FILE_PATH = 'data/prices_round_1_day_0.csv'
TRADES_OUTPUT_FILE_PATH = 'data/trades_round_1_simulator.csv'
df = pd.read_csv(INPUT_FILE_PATH, delimiter=';')
df.set_index('timestamp')

# Initialize necessary variables for TradingState
CURRENCY = 'SEASHELLS'
commodities = ['PEARLS', 'BANANAS']
listings = { c:Listing(c, c, CURRENCY) for c in commodities } # not used for now
own_trades = { c:[] for c in commodities } # using
market_trades = { } # not used
observations = {} # not used
position = { c:0 for c in commodities } # using

# Variables for the simulator
position_limits = {'PEARLS': 20, 'BANANAS': 20}
own_trades_custom = [] # Saves whether the trade was buy or sell


# simulate for one day with 10000 timesteps
for i in range(0, 1000000, 100):
    curr_time_df = df[df['timestamp'] == int(i)]
    order_depths = {}

    for c in commodities:
        curr_df = curr_time_df[curr_time_df['product'] == c].iloc[0]

        # Load bot orders
        order_depth = OrderDepth()
        if not pd.isnull(curr_df['bid_price_1']):
            order_depth.buy_orders[int(curr_df['bid_price_1'])] = int(curr_df['bid_volume_1'])
        if not pd.isnull(curr_df['bid_price_2']):
            order_depth.buy_orders[int(curr_df['bid_price_2'])] = int(curr_df['bid_volume_2'])
        if not pd.isnull(curr_df['bid_price_3']):
            order_depth.buy_orders[int(curr_df['bid_price_3'])] = int(curr_df['bid_volume_3'])
        if not pd.isnull(curr_df['ask_price_1']):
            order_depth.sell_orders[int(curr_df['ask_price_1'])] = int(-curr_df['ask_volume_1'])
        if not pd.isnull(curr_df['ask_price_2']):
            order_depth.sell_orders[int(curr_df['ask_price_2'])] = int(-curr_df['ask_volume_2'])
        if not pd.isnull(curr_df['ask_price_3']):
            order_depth.sell_orders[int(curr_df['ask_price_3'])] = int(-curr_df['ask_volume_3'])

        order_depths[c] = order_depth
    

    state = TradingState(i, listings, order_depths, own_trades, market_trades, position, observations)
    order_list = trader.run(state)
    
    for c in commodities:
        c_order_list = order_list[c]
        for order in c_order_list:
            # BUY order
            if order.quantity > 0:
                if order.price in order_depths[c].sell_orders:
                    # Check how many can be fulfilled
                    fulfilled_volume = min(position_limits[c] - position[c], abs(order_depths[c].sell_orders[order.price]), order.quantity)
                    # print("SIMULATOR BUYING " + str(c) + " " + str(fulfilled_volume) + " at " + str(order.price))
                    
                    # Execute BUY order
                    buy_trade = Trade(c, order.price, fulfilled_volume, None, None, i)
                    position[c] += fulfilled_volume
                    own_trades[c].append(buy_trade)
                    own_trades_custom.append([buy_trade, 'BUY', position[c]])
                    assert(abs(position[c]) <= position_limits[c])

            # SELL order
            elif order.quantity < 0:
                if order.price in order_depths[c].buy_orders:
                    fulfilled_volume = min(position_limits[c] + position[c], abs(order_depths[c].buy_orders[order.price]), -order.quantity)
                    # print("SIMULATOR SELLING " + str(c) + " " + str(fulfilled_volume) + " at " + str(order.price))

                    # Execute SELL order
                    sell_trade = Trade(c, order.price, fulfilled_volume, None, None, i)
                    position[c] -= fulfilled_volume
                    own_trades[c].append(sell_trade)
                    own_trades_custom.append([sell_trade, 'SELL', position[c]])
                    assert(abs(position[c]) <= position_limits[c])


# Save trade information in a custom format csv, that includes BUY/SELL information
trades_df = pd.DataFrame(columns=['timestamp', 'buyer', 'seller', 'symbol', 'currency', 'price', 'quantity', 'operation', 'position'])
for t in own_trades_custom:
    trades_df.loc[len(trades_df)] = [t[0].timestamp, t[0].buyer, t[0].seller, t[0].symbol, CURRENCY, t[0].price, t[0].quantity, t[1], t[2]]

trades_df.to_csv(TRADES_OUTPUT_FILE_PATH)
print(trades_df)