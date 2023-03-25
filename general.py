from typing import Callable, Dict, List
from copy import deepcopy
import numpy as np
from statistics import mean
from datamodel import OrderDepth, TradingState, Order

from bananas import Trader as BananasTrader

b = BananasTrader()

def helper(states):
    return {c: sum([t.quantity for t in trades]) for c, trades in b.run(states[-1]).items()}


CLASSIFIER = helper

class Trader:


    def __init__(self, cls : Callable = CLASSIFIER, verbose = False):
        self.time : int = 0
        self.states : List[Dict] = []
        self.cls = cls
        self.limits = {
            "PEARLS": 20,
            "BANANAS": 20,
            "COCONUTS": 600,
            "PINA_COLADAS": 300,
            "DIVING_GEAR": 50,
            "BERRIES": 250,
            "DOLPHIN_SIGHTINGS": 0
        }
        self.hard_limit = False
        self.verbose = verbose


    def run(self, state: TradingState) -> Dict[str, List[Order]]:


        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        
        # Compute changes in state
        position = deepcopy(state.position)
        for product in state.order_depths.keys():
            if not product in position:
                position[product] = 0

        self.add_state(state)
        diffs = self.cls(self.states)

        # Iterate over all the keys (the available products) contained in the order depths
        result = {}
        for product in state.order_depths.keys():

            if not product in diffs:
                continue
            
            diff = diffs[product]
            
            if abs(position[product] + diff) > self.limits[product]:
                if self.hard_limit:
                    raise Exception(f"Position limit exceeded for {product}: old_position={position[product]}, diff={diff}")
                else:
                    diff = max(diff, -self.limits[product] - position[product])
                    diff = min(diff, self.limits[product] - position[product])
                    diffs[product] = diff
            
            if diff > 0:
                result[product] = self.buy(product, diff, state.order_depths[product])
            elif diff < 0:
                result[product] = self.sell(product, -diff, state.order_depths[product])

        self.time += 1

        if self.verbose:
            print(position)
            print(result)

        return result

    
    def add_state(self, state: TradingState):
        self.states.append(state)

        if self.verbose:
            print(state.toJSON())


    def buy(self, product : str, n : int, order_depth):

        # Iterate over offers
        orders = []
        for ask_price in sorted(order_depth.sell_orders.keys()):
            
            # Compute volume for one trade
            ask_volume = -order_depth.sell_orders[ask_price]
            curr_volume = min(n, ask_volume)

            # print("Sell orders :", order_depth.sell_orders)
            # print("Buy", product, ask_volume, n, curr_volume, ask_price, Order(product, ask_price, curr_volume))
            
            # Place order
            orders.append(Order(product, ask_price, curr_volume))

            # Update volume needed
            n -= curr_volume
            if n == 0:
                break
        return orders


    def sell(self, product : str, n : int, order_depth):

        # Iterate over offers
        orders = []
        for bid_price in sorted(order_depth.buy_orders.keys(), reverse=True):
            
            # Compute volume for one trade
            bid_volume = order_depth.buy_orders[bid_price]
            curr_volume = min(n, bid_volume)

            # print("Buy orders :", order_depth.buy_orders)
            # print("Sell", product, bid_volume, n, curr_volume, bid_price, Order(product, bid_price, -curr_volume))
            
            # Place order
            orders.append(Order(product, bid_price, -curr_volume))

            # Update volume needed
            n -= curr_volume
            if n == 0:
                break

        return orders