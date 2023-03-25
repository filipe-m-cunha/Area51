import argparse
import numpy as np
import pandas as pd
from datamodel import OrderDepth, TradingState, Order, Listing, Trade
from typing import Dict, List
from tqdm.auto import tqdm

#! change this import to get the newest Trader
from general import Trader

# should amount to implementing the Wiki:
# https://imc-prosperity.notion.site/Writing-an-Algorithm-in-Python-c44b46f32941430fa1eccb6ff054be26

# our trader
trader = Trader()

position_limits = {
    "PEARLS": 20,
    "BANANAS": 20,
    "COCONUTS": 600,
    "PINA_COLADAS": 300,
    "DIVING_GEAR": 50,
    "BERRIES": 250
}
commodities = list(position_limits.keys())

INPUT_FILE_PATH = 'data/prices_round_3_day_0.csv'
#INPUT_FILE_PATH = 'data/tutorial_data.csv'
#TRADES_OUTPUT_FILE_PATH = 'data/trades_round_1_day_0_simulator.csv'
TRADES_OUTPUT_FILE_PATH = 'data/trades_round2_simulator.csv'
PRICES_OUTPUT_FILE_PATH = 'data/prices_round2_simulator.csv'
df = pd.read_csv(INPUT_FILE_PATH, delimiter=';')
df.set_index('timestamp')

# Initialize necessary variables for TradingState
CURRENCY = 'SEASHELLS'
listings = { c:Listing(c, c, CURRENCY) for c in commodities } # not used for now
own_trades = { c:[] for c in commodities } # using
market_trades = { } # not used
observations = {} # not used
position = { c:0 for c in commodities } # using

# Variables for the simulator
own_trades_custom = [] # Saves whether the trade was buy or sell
long_positions = { c:[] for c in commodities }
short_positions = { c:[] for c in commodities}
cumulative_profit = { c:0 for c in commodities }

# simulate for one day with 10000 timesteps
# number below should be 200000 for tutorial and 1000000 for round 1
TIME_STEP = 100
MAX_TIME = TIME_STEP * df.shape[0]
for i in tqdm(range(0, MAX_TIME, TIME_STEP)):
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
        if c in order_list:
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
                        own_trades[c].append(buy_trade)


                        # Update internal positions list
                        remaining_buy_quantity = fulfilled_volume
                        # close short positions first
                        if len(short_positions[c]) > 0:
                            assert(len(short_positions[c]) == abs(position[c]))
                            short_close_quantity = min(len(short_positions[c]), remaining_buy_quantity)
                            cumulative_profit[c] += sum(short_positions[c][:short_close_quantity]) - short_close_quantity * order.price
                            short_positions[c] = short_positions[c][short_close_quantity:]
                            remaining_buy_quantity -= short_close_quantity
                            position[c] += short_close_quantity
                            assert(len(short_positions[c]) == abs(position[c]))
                        # open long positions
                        if len(short_positions[c]) == 0 and remaining_buy_quantity > 0:
                            assert(len(long_positions[c]) == position[c])
                            long_positions[c].extend([order.price for x in range(remaining_buy_quantity)])
                            position[c] += remaining_buy_quantity
                            remaining_buy_quantity = 0
                            assert(len(long_positions[c]) == position[c])

                        own_trades_custom.append([buy_trade, 'BUY', position[c], cumulative_profit[c], long_positions[c], short_positions[c]])
                        #position[c] += fulfilled_volume
                        assert(abs(position[c]) <= position_limits[c])

                # SELL order
                elif order.quantity < 0:
                    if order.price in order_depths[c].buy_orders:
                        fulfilled_volume = min(position_limits[c] + position[c], abs(order_depths[c].buy_orders[order.price]), -order.quantity)
                        # print("SIMULATOR SELLING " + str(c) + " " + str(fulfilled_volume) + " at " + str(order.price))

                        # Execute SELL order
                        sell_trade = Trade(c, order.price, fulfilled_volume, None, None, i)
                        own_trades[c].append(sell_trade)

                        # Update internal positions list
                        remaining_sell_quantity = fulfilled_volume
                        # close long positions first
                        if len(long_positions[c]) > 0:
                            assert(len(long_positions[c]) == position[c])
                            long_close_quantity = min(len(long_positions[c]), remaining_sell_quantity)
                            cumulative_profit[c] += long_close_quantity * order.price - sum(long_positions[c][:long_close_quantity])
                            long_positions[c] = long_positions[c][long_close_quantity:]
                            remaining_sell_quantity -= long_close_quantity
                            position[c] -= long_close_quantity
                        # open short positions
                        if len(long_positions[c]) == 0:
                            assert(len(short_positions[c]) == abs(position[c]))
                            short_positions[c].extend([order.price for x in range(remaining_sell_quantity)])
                            position[c] -= remaining_sell_quantity
                            remaining_sell_quantity = 0
                            assert(len(short_positions[c]) == abs(position[c]))

                        own_trades_custom.append([sell_trade, 'SELL', position[c], cumulative_profit[c], long_positions[c], short_positions[c]])
                        assert(abs(position[c]) <= position_limits[c])

        df.loc[(df['timestamp'] == i) & (df['product'] == c), 'profit_and_loss'] = cumulative_profit[c]


# Save trade information in a custom format csv, that includes BUY/SELL information
trades_df = pd.DataFrame(columns=['timestamp', 'buyer', 'seller', 'symbol', 'currency', 'price', 'quantity', 'operation', 'position', 'profit', 'long_positions', 'short_positions'])
for t in own_trades_custom:
    trades_df.loc[len(trades_df)] = [t[0].timestamp, t[0].buyer, t[0].seller, t[0].symbol, CURRENCY, t[0].price, t[0].quantity, t[1], t[2], t[3], t[4], t[5]]

trades_df.to_csv(TRADES_OUTPUT_FILE_PATH)
print(trades_df)

df.to_csv(PRICES_OUTPUT_FILE_PATH, sep=';')
print(df)
