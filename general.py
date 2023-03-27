from typing import Callable, Dict, List
from copy import deepcopy
import numpy as np
from statistics import mean, median
from datamodel import OrderDepth, TradingState, Order

class CocoPinaCls:
    def __init__(self):
        self.limits = {
          "COCONUTS": 600,
          "PINA_COLADAS": 300
        }
        self.beta = 0.5331881677582299
        
        self.lag = 5
        self.slope_lag = 5
        self.spreads = []
        self.time = 0
        
    def __call__(self, states : List[Dict]):
        pina_state = states[-1]
        
        if self.time >= self.lag:
            coco_state = states[-1 - self.lag] 
        else:
            coco_state = pina_state
        
        coco_depths = coco_state.order_depths
        # calculate mid price of COCONUTS
        orders_coco = coco_depths['COCONUTS']
        coco_buys = orders_coco.buy_orders
        buys = []
        for buy_price in coco_buys.keys():
            buys += [buy_price] * coco_buys[buy_price]
        median_price_buys = median(buys)
        coco_sells = orders_coco.sell_orders
        sells = []
        for sell_price in coco_sells.keys():
            sells += [sell_price] * (-coco_sells[sell_price])
        median_price_sells = median(sells)
        coco = mean([median_price_buys, median_price_sells])
        
        pina_depths = pina_state.order_depths
        # calculate mid price of PINA_COLADAS
        orders_pina = pina_depths['PINA_COLADAS']
        pina_buys = orders_pina.buy_orders
        buys = []
        for buy_price in pina_buys.keys():
            buys += [buy_price] * pina_buys[buy_price]
        median_price_buys = median(buys)
        pina_sells = orders_pina.sell_orders
        sells = []
        for sell_price in pina_sells.keys():
            sells += [sell_price] * (-pina_sells[sell_price])
        median_price_sells = median(sells)
        pina = mean([median_price_buys, median_price_sells])
        
        # calculate spread
        spread = coco - self.beta * pina
        if self.spreads == [] or self.spreads[-1] != spread:
            self.spreads.append(spread)
            self.time += 1
            
        if self.time >= 30 and self.time % 5 == 0 and spread < 0 and spread - self.spreads[-5] < 0:
            return {'COCONUTS': -300, 'PINA_COLADAS': 0}
        elif self.time >= 30 and self.time % 5 == 0 and spread > 0 and spread - self.spreads[-5] > 0:
            return {'COCONUTS': 0, 'PINA_COLADAS': -300}
        
        # if spread is negative, PINA_COLADAS are overpriced, otherwise COCONUTS are
        if spread < 0:
            # long cocos, short pinas, go BOLD
            if abs(spread) > 20:
                return {'COCONUTS': 10, 'PINA_COLADAS': -10}
            else:
                return {'COCONUTS': 5, 'PINA_COLADAS': -5}
        else:
            if abs(spread) > 20:
                return {'COCONUTS': -10, 'PINA_COLADAS': 10}
            else:
                return {'COCONUTS': -50, 'PINA_COLADAS': 5}

class Trader:

    def __init__(self, verbose = False):
        self.time : int = 0
        self.states : List[Dict] = []
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
        
        coco_pina_cls = CocoPinaCls()
        
        # Iterate over all the keys (the available products) contained in the order depths
        result = {}
        for product in state.order_depths.keys():
            
            if product == 'COCONUTS' or product == 'PINA_COLADAS':
                diffs = coco_pina_cls(self.states)
            else:
                diffs = None

            if diffs is None or not product in diffs:
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