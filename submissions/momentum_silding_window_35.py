from typing import Dict, List
import numpy as np
from statistics import mean
from datamodel import OrderDepth, TradingState, Order


PRINT_BANANA_ASK_STATS = True
PRINT_BANANA_BID_STATS = True
PRINT_PEARL_ASK_STATS = False
PRINT_PEARL_BID_STATS = False
MAX_CONCURRENT_POSITION = 20
MAX_POSITION_PERCENT = 0.2
STOP_LOSS_PERCENT = 0.1
TAKE_PROFIT_PERCENT = 0.2
MOMENTUM_WINDOW_SIZE = 5
STAT_SLIDING_WINDOW_SIZE = 3

def get_mean_price(orders):
    if len(orders) > 0:
        return mean(orders.keys())
    else:
        return None


class Trader:

    def __init__(self):
        #Keeping these varaibles hardcoded for now, we will probably need to change them
        self.max_concurrent_positions = MAX_CONCURRENT_POSITION
        self.max_position_percent = MAX_POSITION_PERCENT
        self.stop_loss_percent = STOP_LOSS_PERCENT
        self.take_profit_percent = TAKE_PROFIT_PERCENT
        self.momentum_factor = MOMENTUM_WINDOW_SIZE
        self.bid_history = []
        self.ask_history = []
        self.banana_ask_stats = SlidingWindowStatistics(STAT_SLIDING_WINDOW_SIZE, "BANANA ASK")
        self.banana_bid_stats = SlidingWindowStatistics(STAT_SLIDING_WINDOW_SIZE, "BANANA BID")
        self.pearl_ask_stats = SlidingWindowStatistics(STAT_SLIDING_WINDOW_SIZE, "PEARL ASK")
        self.pearl_bid_stats = SlidingWindowStatistics(STAT_SLIDING_WINDOW_SIZE, "PEARL BID")
        self.banana_long_positions = []
        self.banana_short_positions = []

    def run(self, state: TradingState) -> Dict[str, List[Order]]:


        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        result = {}

        # Iterate over all the keys (the available products) contained in the order depths
        for product in state.order_depths.keys():

            # Check if the current product is the 'PEARLS' product, only then run the order logic
            if product == 'PEARLS':

                # Retrieve the Order Depth containing all the market BUY and SELL orders for PEARLS
                order_depth: OrderDepth = state.order_depths[product]

                # Initialize the list of Orders to be sent as an empty list
                orders: list[Order] = []
                acceptable_price = 10000

                # For stats calculation
                if PRINT_PEARL_ASK_STATS:
                    self.pearl_ask_stats.add(order_depth.sell_orders)
                if PRINT_PEARL_BID_STATS:
                    self.pearl_bid_stats.add(order_depth.buy_orders)

                if len(order_depth.sell_orders) > 0:
                    # Sort and check whether any orders
                    for ask_price in sorted(order_depth.sell_orders.keys()):
                        if ask_price >= acceptable_price:
                            break
                        ask_volume = order_depth.sell_orders[ask_price]
                        print("BUY PEARLS", str(-ask_volume) + "x", ask_price)
                        orders.append(Order(product, ask_price, -ask_volume))
                if len(order_depth.buy_orders) != 0:
                    for ask_price in sorted(order_depth.buy_orders.keys(), reverse=True):
                        if ask_price <= acceptable_price:
                            break
                        ask_volume = order_depth.buy_orders[ask_price]
                        print("SELL PEARLS", str(ask_volume) + "x", ask_price)
                        orders.append(Order(product, ask_price, -ask_volume))
                result[product] = orders

            if product == 'BANANAS':
                order_depth: OrderDepth = state.order_depths[product]
                orders: list[Order] = []

                # For stats calculation
                if PRINT_BANANA_ASK_STATS:
                    self.banana_ask_stats.add(order_depth.sell_orders)
                if PRINT_BANANA_BID_STATS:
                    self.banana_bid_stats.add(order_depth.buy_orders)

                #mean_ask_price = min(order_depth.sell_orders.keys())
                #mean_bid_price = max(order_depth.buy_orders.keys())
                mean_ask_price = self.banana_ask_stats.get_mean()
                mean_bid_price = self.banana_bid_stats.get_mean()

                should_buy = self.banana_ask_stats.should_act(mean_ask_price, buy = True)
                should_sell = not self.banana_ask_stats.should_act(mean_bid_price, buy = False)

                if len(order_depth.buy_orders) > 0:
                    num_positions = 0 if 'BANANAS' not in state.position.keys() else state.position['BANANAS']
                    can_short = True
                    print("bot bid depths: " + str(order_depth.buy_orders))
                    for bid_price in sorted(order_depth.buy_orders.keys(), reverse=True):
                        if bid_price > np.mean(np.array(self.banana_long_positions)):
                            can_short = False
                            bid_volume = min(order_depth.buy_orders[bid_price], num_positions)
                            print("SELL BANANAS", str(bid_volume) + "x", bid_price)
                            orders.append(Order(product, bid_price, -bid_volume))
                            num_positions -= bid_volume
                            self.banana_long_positions = self.banana_long_positions[bid_volume:]

                if len(order_depth.sell_orders) > 0:
                    num_positions = 0 if 'BANANAS' not in state.position.keys() else state.position['BANANAS']

                    print("bot ask depths: " + str(order_depth.sell_orders))
                    for ask_price in sorted(order_depth.sell_orders.keys()):
                        if ask_price <= self.banana_bid_stats.get_eightith() and len(self.banana_ask_stats.sliding_window) > 2:
                            ask_volume = max(order_depth.sell_orders[ask_price], -(20 - (num_positions)))
                            print("BUY BANANAS", str(-ask_volume) + "x", ask_price)
                            orders.append(Order(product, ask_price, -ask_volume))
                            num_positions -= ask_volume
                            self.banana_long_positions += [ask_price for x in range(abs(ask_volume))]


                # Add all the above orders to the result dict
                result[product] = orders


                # Return the dict of orders
                # These possibly contain buy or sell orders for PEARLS
                # Depending on the logic above

        
        print(state.position)
        print(self.banana_long_positions)

        # Print stats
        if PRINT_BANANA_ASK_STATS:
            self.banana_ask_stats.print_stats()
        if PRINT_BANANA_BID_STATS:
            self.banana_bid_stats.print_stats()
        if PRINT_PEARL_ASK_STATS:
            self.pearl_ask_stats.print_stats()
        if PRINT_PEARL_BID_STATS:
            self.pearl_bid_stats.print_stats()
        return result

class SlidingWindowStatistics:

    def __init__(self, sliding_window_size, statistics_type):
        self.sliding_window_size = sliding_window_size
        self.sliding_window = []
        self.statistics_type = statistics_type
        self.mean = 10000
        self.flat_list = []

    def add(self, order_depth):
        self.sliding_window.append(order_depth)
        if len(self.sliding_window) > self.sliding_window_size:
            self.sliding_window = self.sliding_window[-self.sliding_window_size:]

    # Outputs flat sorted list of orders in the sliding window
    def flatten(self):
        flat_list = []
        for order_depth_dict in self.sliding_window:
            for price in order_depth_dict:
                flat_list.extend([price for x in range(abs(order_depth_dict[price]))])


        flat_list.sort()
        return flat_list

    def should_act(self, curr_price, buy = True):
        order_depth_dict = self.sliding_window[0]
        if buy:
            min_momentum_price = min([price for price in order_depth_dict])
        else:
            min_momentum_price = max([price for price in order_depth_dict])
        momentum = curr_price - min_momentum_price
        if momentum > 0:
            return True
        else:
            return False

    def update_stats(self):
        self.flat_list = self.flatten()
        self.mean = int(sum(self.flat_list) / max(1,len(self.flat_list)))

    def get_mean(self):
        return self.mean

    def get_eightith(self):
        if len(self.flat_list) > 0:
            return self.flat_list[max(0,len(self.flat_list) - 1 - int(len(self.flat_list)/5))]
        else:
            return 0

    def print_stats(self):
        self.update_stats()
        flat_list = self.flat_list
        #print(flat_list)
        if len(flat_list) > 10:
            output = "[" + str(self.statistics_type) + ","
            output += "mean:" + str(self.mean) + ","
            output += "min:" + str(flat_list[0]) + ","
            output += "10th:" + str(flat_list[int(len(flat_list)/10)]) + ","
            output += "25th:" + str(flat_list[int(len(flat_list)/4)]) + ","
            output += "50th:" + str(flat_list[int(len(flat_list)/2)]) + ","
            output += "75th:" + str(flat_list[max(0,len(flat_list) - 1 - int(len(flat_list)/4))]) + ","
            output += "90th:" + str(flat_list[max(0,len(flat_list) - 1 - int(len(flat_list)/10))]) + ","
            output += "max:" + str(flat_list[-1:]) + ","
            output += "vol:" + str(len(flat_list))
            output += "]"
        else:
            output= "[" + str(self.statistics_type) + ", more data needed]"

        print(output)
