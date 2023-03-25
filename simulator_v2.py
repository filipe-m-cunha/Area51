import argparse
from turtle import pos, position
import numpy as np
import pandas as pd
from pathlib import Path
from datamodel import OrderDepth, TradingState, Order, Listing, Trade
from typing import Dict, List
from tqdm.auto import tqdm

#! change this import to get the newest Trader
from trader import Trader

# def line_to_state()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--in_file", type=Path)
    parser.add_argument("--n_bots", type=int, default=3)
    # parser.add_argument("--out_file", type=Path)
    args = parser.parse_args()
    nbots = args.n_bots


    # our trader
    trader = Trader()
    commodities = list(trader.limits.keys())

    df = pd.read_csv(args.in_file, sep=";").groupby(by=["timestamp"])
    position = {c: 0 for c in trader.limits}
    gain = 0


    for time, timestamp in tqdm(df):

        # Create the orders
        order_depths = {}
        for row in timestamp.to_dict(orient="records"):

            c = row["product"]

            # Load bot orders
            order_depth = OrderDepth()
            for i in range(1, nbots + 1):

                # Add buy orders
                if not pd.isnull(row[f"bid_price_{i}"]):

                    if not int(row[f"bid_price_{i}"]) in order_depth.buy_orders:
                        order_depth.buy_orders[int(row[f"bid_price_{i}"])] = 0

                    order_depth.buy_orders[int(row[f"bid_price_{i}"])] += int(row[f"bid_volume_{i}"])
                
                # Add ask offerings
                if not pd.isnull(row[f"ask_price_{i}"]):

                    if not int(row[f"ask_price_{i}"]) in order_depth.sell_orders:
                        order_depth.sell_orders[int(row[f"ask_price_{i}"])] = 0

                    order_depth.sell_orders[int(row[f"ask_price_{i}"])] -= int(row[f"ask_volume_{i}"])

            order_depths[c] = order_depth
        
        # Get state
        state = TradingState(time, {}, order_depths, {}, {}, position, {})

        # Update state
        for c, trades in trader.run(state).items():
            for trade in trades:
                position[c] += trade.quantity
                gain -= trade.quantity * trade.price

    # Get to zero state
    
    print(gain)
    print(position)
    for row in timestamp.to_dict(orient="records"):
        if position[row["product"]] != 0:
            if position[row["product"]] < 0:
                price = min([row[f"ask_price_{i}"] for i in range(1, nbots + 1) if not pd.isnull(row[f"ask_price_{i}"])])
            else:
                price = max([row[f"buy_price_{i}"] for i in range(1, nbots + 1) if not pd.isnull(row[f"buy_price_{i}"])])
            gain += position[row["product"]] * price
            position[row["product"]] = 0

    print(gain)
