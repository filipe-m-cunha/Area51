import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--data', type=str, required=True)

args = parser.parse_args()
data = pd.read_csv(args.data, sep=';')

products = data['product'].unique()
fig, ax = plt.subplots(nrows=4, ncols=len(products), figsize=(6, 10))
i = 0
for product in products:
    product_data = data[data['product'] == product]
    
    # mid price
    ax[0, i].plot(product_data['mid_price'], lw=0.3)
    ax[0, i].set_title('Mid price')
    
    # profits
    ax[1, i].plot(product_data['profit_and_loss'], lw=0.3)
    ax[1, i].set_title('Profits and Losses')
    
    # avg bids/asks
    bids_asks = product_data.iloc[:, 3:-2:2]
    avg_bids = bids_asks.iloc[:, :len(bids_asks.columns) // 2].mean(axis=1)
    avg_asks = bids_asks.iloc[:, len(bids_asks.columns) // 2:].mean(axis=1)
    ax[2, i].plot(avg_bids, label='Average bids', lw=0.3)
    ax[2, i].plot(avg_asks, label='Average asks', lw=0.3)
    ax[2, i].legend()
    ax[2, i].set_title('Bids/Asks')
    
    # volume
    volumes = product_data.iloc[:, 4:-2:2]
    bid_volume = volumes.iloc[:, :len(volumes.columns) // 2].mean(axis=1)
    ask_volume = volumes.iloc[:, len(volumes.columns) // 2:].mean(axis=1)
    ax[3, i].plot(bid_volume, label='Bids', lw=0.3)
    ax[3, i].plot(ask_volume, label='Asks', lw=0.3)
    ax[3, i].legend()
    ax[3, i].set_title('Volume')
    
    i += 1
    
plt.tight_layout()
plt.show()