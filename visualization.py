import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse

VOLUME_BINNING = 25

def get_last_profit_loss(data, products):
    list_last_profit_loss = []
    for product in products:
        last_profit_loss = data[data['product'] == product]['profit_and_loss'].iloc[-1]
        list_last_profit_loss.append(last_profit_loss)
    return list_last_profit_loss
    

parser = argparse.ArgumentParser()
parser.add_argument('--data', type=str, required=True, nargs='+')

args = parser.parse_args()
data = pd.read_csv(args.data[0], sep=';')
products = data['product'].unique()
last_profits = get_last_profit_loss(data, products)
for i in range(1, len(args.data)):
    data_ = pd.read_csv(args.data[i], sep=';')
    for product, last_profit in zip(products, last_profits):
        data_prod = data_[data_['product'] == product]
        data_prod['profit_and_loss'] += last_profit
        data_[data_['product'] == product] = data_prod
    last_profits = get_last_profit_loss(data_, products)
    data = pd.concat([data, data_])
    
data['time'] = data['day'] * 1e6 + data['timestamp']

fig, ax = plt.subplots(nrows=4, ncols=len(products), figsize=(6, 10))
i = 0
for product in products:
    product_data = data[data['product'] == product]
    time = product_data['time']
    
    # mid price
    ax[0, i].plot(time, product_data['mid_price'], lw=0.3)
    ax[0, i].set_title(product)
    
    # profits
    ax[1, i].plot(time, product_data['profit_and_loss'], lw=0.3)
    ax[1, i].set_title('Profits and Losses')
    
    # avg bids/asks
    bids_asks = product_data.iloc[:, 3:-2:2]
    avg_bids = bids_asks.iloc[:, :len(bids_asks.columns) // 2].mean(axis=1)
    avg_asks = bids_asks.iloc[:, len(bids_asks.columns) // 2:].mean(axis=1)
    highest_bids = product_data.iloc[:, 4]
    lowest_asks = product_data.iloc[:, 10]
    diff_bid_ask = lowest_asks - highest_bids
    #ax[2, i].plot(time, avg_bids, label='Average bids', lw=0.3)
    #ax[2, i].plot(time, avg_asks, label='Average asks', lw=0.3)
    #ax[2, i].plot(time, highest_bids, label='highest bid', lw=0.3)
    #ax[2, i].plot(time, lowest_asks, label='lowest ask', lw=0.3)
    ax[2, i].plot(time, diff_bid_ask, label='bid ask', lw=0.3)
    ax[2, i].legend()
    ax[2, i].set_title('Bid Ask')
    
    # volume
    volumes = product_data.iloc[:, 4:-2:2]
    bid_volume = volumes.iloc[:, :len(volumes.columns) // 2].sum(axis=1).to_numpy()
    bid_volume = bid_volume.reshape(-1, VOLUME_BINNING)
    bid_volume = bid_volume.sum(axis=1)
    ask_volume = volumes.iloc[:, len(volumes.columns) // 2:].sum(axis=1).to_numpy()
    ask_volume = ask_volume.reshape(-1, VOLUME_BINNING)
    ask_volume = ask_volume.sum(axis=1)
    ax[3, i].plot(bid_volume, label='Bids', lw=0.3)
    ax[3, i].plot(ask_volume, label='Asks', lw=0.3)
    ax[3, i].legend()
    ax[3, i].set_title('Volume')

    
    i += 1
    
plt.tight_layout()
plt.show()