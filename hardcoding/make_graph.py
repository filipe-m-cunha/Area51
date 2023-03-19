from math import isnan
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from pathlib import Path

class StockmarketLog:

    bid_price_token : str = "bid_price_"
    bid_volume_token : str = "bid_volume_"
    ask_price_token : str = "ask_price_"
    ask_volume_token : str = "ask_volume_"

    def __init__(self, filename : Path, max_pos : int):

        # Set params
        self.max_pos = max_pos

        # Load data
        df = pd.read_csv(filename, sep=";")

        # Query number of biders and askers
        # Set number of bots
        nbiders = len([bot for bot in df.columns if StockmarketLog.bid_price_token in bot])
        assert all(StockmarketLog.bid_price_token + str(i + 1) in df.columns for i in range(nbiders))
        assert all(StockmarketLog.bid_volume_token + str(i + 1) in df.columns for i in range(nbiders))

        naskers = len([bot for bot in df.columns if StockmarketLog.ask_price_token in bot])        
        assert all(StockmarketLog.ask_price_token + str(i + 1) in df.columns for i in range(naskers))
        assert all(StockmarketLog.ask_volume_token + str(i + 1) in df.columns for i in range(naskers))

        assert nbiders == naskers
        self.nbots = nbiders

        # Make 
        self.optimal_positions = {
          k: self.make_graph(table, k)
          for k, table in df.groupby("product")
        }      

    def make_graph(self, table : pd.DataFrame, key : str):
        graph = nx.DiGraph()

        t_end = table.shape[0]
        for t in range(t_end + 1):
            self.add_layer(graph, t)
        for t in range(t_end):
            self.add_edges(graph, table, t)

        # p = nx.shortest_path(graph, source="0_0",target=f"{t_end}_0", weight="weight")
        p = nx.bellman_ford_path(graph, source="0_0",target=f"{t_end}_0", weight="weight")

        path = [
          int(pos.split("_")[-1])
          for pos in p
        ]

        cost = nx.get_edge_attributes(graph,'cost')
        total = 0
        for prev, curr in zip(p[:-1], p[1:]):
            total += cost[(prev, curr)]
        print(total)
        
        # plt.figure(3,figsize=(60,12)) 

        # edges = graph.edges()
        # special = [(u, v) for u, v in zip(p[:-1], p[1:])]
        # colors = [("red" if (u, v) in special else "black") for u,v in edges]

        # pos=nx.get_node_attributes(graph,'pos')
        # labels = nx.get_edge_attributes(graph,'cost')
        # nx.draw(graph, pos, node_size=150, node_color='blue', font_size=6, font_weight='bold', edge_color=colors)
        # nx.draw_networkx_edge_labels(graph,pos,edge_labels=labels, label_pos=0.25)
        # plt.savefig(f"Graph_{key}.png", format="PNG")

        return path

    
    def add_layer(self, graph : nx.DiGraph, t : int):
        for i in range(-self.max_pos, self.max_pos + 1):
            graph.add_node(f"{t}_{i}", pos=(t,i))


    def add_edges(self, graph : nx.DiGraph, table : pd.DataFrame, t : int):
        
        line = table.iloc[t]
        bids = self.get_positions(StockmarketLog.bid_price_token, StockmarketLog.bid_volume_token, line)
        bids.sort(reverse=True)
        bids_cum = np.cumsum(bids).tolist()

        asks = self.get_positions(StockmarketLog.ask_price_token, StockmarketLog.ask_volume_token, line)
        asks.sort()
        asks_cum = np.cumsum(asks).tolist()

        # Add edges for each node
        for i in range(-self.max_pos, self.max_pos + 1):
            self.add_edges_from_node(graph, i, t, bids_cum, asks_cum)


    def get_positions(self, price_token : str, volume_token : str, line : pd.DataFrame):

        # Represents positions as list of floats
        positions = []

        # Add position from all bots
        for bot in range(1, self.nbots + 1):
            bid_price = line[price_token + str(bot)]
            bid_volume = line[volume_token + str(bot)]

            if not isnan(bid_price) and not isnan(bid_volume):
                positions.extend([float(bid_price)] * int(bid_volume))

        return positions


    def add_edges_from_node(self, graph : nx.DiGraph, i : int, t : int, bids_cum : list, asks_cum : list):

        graph.add_edge(f"{t}_{i}", f"{t + 1}_{i}", weight=0.0, cost=0.0)

        for delta, j in enumerate(range(i + 1, self.max_pos + 1)[:len(asks_cum)]):
            graph.add_edge(
                f"{t}_{i}", f"{t + 1}_{j}", 
                weight=asks_cum[delta],
                cost=-asks_cum[delta]
            )

        for delta, j in enumerate(range(i - 1, -self.max_pos - 1, -1)[:len(bids_cum)]):
            graph.add_edge(
                f"{t}_{i}", f"{t + 1}_{j}", 
                weight=-bids_cum[delta],
                cost=bids_cum[delta]
            )

import json
if __name__ == "__main__":
    json.dump(
        StockmarketLog("1370d8be-d8f3-4142-8ac8-6cbcd8b3661b.csv", 20).optimal_positions,
        open("trades.json", "w")
    )
