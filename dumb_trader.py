from typing import Dict, List
import numpy as np
from statistics import mean
from datamodel import OrderDepth, TradingState, Order


def get_mean_price(orders):
    if len(orders) > 0:
        return mean(orders.keys())
    else:
        return None


class Trader:

    def __init__(self):
        pass

    def run(self, state: TradingState) -> Dict[str, List[Order]]:


        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        result = {}

        return result
