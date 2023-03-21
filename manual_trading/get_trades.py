import argparse
from typing import Dict
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from pathlib import Path
import json


def bellman_ford(G : nx.DiGraph, start : str, n_iter : int):

    nx.set_node_attributes(G, {start: 1}, name="gain")
    nx.set_node_attributes(G, {start: [start]}, name="path")
    prices = nx.get_edge_attributes(G, "price")

    for _ in range(n_iter):
        gains = nx.get_node_attributes(G, name="gain")
        path_old = nx.get_node_attributes(G, name="path")

        for p1, p2 in G.edges:
            
            gain_new = gains[p1] * prices[(p1, p2)]
            gain_old = nx.get_node_attributes(G, name="gain")[p2]
            
            if gain_new > gain_old:                
                nx.set_node_attributes(G, {p2: gain_new}, name="gain")
                nx.set_node_attributes(G, {p2: path_old[p1] + [p2]}, name="path")
    

def make_graph(data : Dict, radius = 10):

    # Extract information
    products, prices = data["products"], data["prices"]
    
    # Build graph
    G = nx.DiGraph()

    # Add nodes from the products
    for i, p in enumerate(products):

        # Compute angle to ensure nice distribution of the nodes
        angle = 2 * np.pi * i / len(products)

        # Add node with gain and prev attributes
        G.add_node(
            p, 
            gain=0, path=[], 
            pos=(radius * np.cos(angle), radius * np.sin(angle))
        )
    
    # Add edges based on prices
    for p1, p1_prices in zip(products, prices):
        for p2, price in zip(products, p1_prices):
            if p1 != p2:
                G.add_edge(p1, p2, price=price)

    return G


def draw(G : nx.DiGraph, start : str, out_file : Path):

    
    pos=nx.get_node_attributes(G,'pos')
    
    # Draw the nodes
    nx.draw_networkx_nodes(G, pos, node_size=1500)

    # Add label indicating optimal gain when ending in each product
    labels = {
        key: f"{key}:\n{value :0.3f}" 
        for key, value in nx.get_node_attributes(G, name="gain").items()
    }
    nx.draw_networkx_labels(G, pos, font_size=8, labels=labels)
    
    # Draw the edges with colored optimal path colored in
    path = nx.get_node_attributes(G, name="path")[start]
    path_edges = [(p1, p2) for p1, p2 in zip(path[:-1], path[1:])]
    color = [("red" if e in path_edges else "black") for e in G.edges]
    nx.draw_networkx_edges(
        G, pos,
        connectionstyle="arc3,rad=0.1",
        min_target_margin=20,
        edge_color=color
    )

    # Add labels indicating the gain from each trade
    nx.draw_networkx_edge_labels(
        G, pos, 
        edge_labels=nx.get_edge_attributes(G,"price"), 
        label_pos=0.25,
    )

    plt.savefig(out_file, format="PNG", dpi=300)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--filename', type=Path)
    parser.add_argument('--out_file', type=Path, default=Path("manual_trade.png"))
    parser.add_argument('--start', type=str, default="Shells")
    parser.add_argument('--n_iter', type=int, default=5)
    args = parser.parse_args()

    # Load json with data
    data = json.load(open(args.filename, "r"))
    if not args.start in data["products"]:
        raise ValueError(f"start must be in {set(data['products'])}")

    # Make graph
    G = make_graph(data)
    bellman_ford(G, args.start, args.n_iter)

    path_string = " -> ".join(nx.get_node_attributes(G, name="path")[args.start])
    print(f"Optimal strategy:\t{path_string}")
    print(f"Optimal gain:\t\t{nx.get_node_attributes(G, name='gain')[args.start] :.5}")

    # Draw graph
    draw(G, args.start, args.out_file)
