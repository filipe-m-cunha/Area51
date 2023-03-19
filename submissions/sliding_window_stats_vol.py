from typing import Dict, List
import numpy as np
from statistics import mean
from datamodel import OrderDepth, TradingState, Order


PRINT_BANANA_ASK_STATS = True
PRINT_BANANA_BID_STATS = False
PRINT_PEARL_ASK_STATS = False
PRINT_PEARL_BID_STATS = False
STAT_SLIDING_WINDOW_SIZE = 30

def get_mean_price(orders):
    if len(orders) > 0:
        return mean(orders.keys())
    else:
        return None


class Trader:

    def __init__(self):
        #Keeping these varaibles hardcoded for now, we will probably need to change them
        self.max_concurrent_positions = 20
        self.max_position_percent = 0.2
        self.stop_loss_percent = 0.1
        self.take_profit_percent = 0.2
        self.momentum_factor = 5
        self.bid_history = []
        self.ask_history = []
        self.banana_ask_stats = SlidingWindowStatistics(STAT_SLIDING_WINDOW_SIZE, "BANANA ASK")
        self.banana_bid_stats = SlidingWindowStatistics(STAT_SLIDING_WINDOW_SIZE, "BANANA BID")
        self.pearl_ask_stats = SlidingWindowStatistics(STAT_SLIDING_WINDOW_SIZE, "PEARL ASK")
        self.pearl_bid_stats = SlidingWindowStatistics(STAT_SLIDING_WINDOW_SIZE, "PEARL BID")

    def get_acceptable_price(self, order_depth, mean_ask_price, mean_bid_price):
        if mean_ask_price is None:
            return None, max(order_depth.buy_orders)
        if mean_bid_price is None:
            return min(order_depth.sell_orders), None
        #Get momentum of the product, aka
        ask_history_arr = np.array(self.ask_history[-self.momentum_factor:])
        bid_history_arr = np.array(self.bid_history[-self.momentum_factor:])
        moving_average_ask = np.mean(ask_history_arr) if len(ask_history_arr) > 0 else None
        moving_average_bid = np.mean(bid_history_arr) if len(bid_history_arr) > 0 else None
        momentum_ask = ask_history_arr[-1] - moving_average_ask
        momentum_bid = bid_history_arr[-1] - moving_average_bid

        if moving_average_ask is None or moving_average_bid is None:
            return None, None

        if momentum_bid < 0:
            acceptable_price_buy = moving_average_bid
        else:
            acceptable_price_buy = mean_bid_price

        if momentum_ask > 0:
            acceptable_price_sell = moving_average_ask
        else:
            acceptable_price_sell = mean_ask_price

        return acceptable_price_buy, acceptable_price_sell

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
                        print("BUY", str(-ask_volume) + "x", ask_price)
                        orders.append(Order(product, ask_price, -ask_volume))
                if len(order_depth.buy_orders) != 0:
                    for ask_price in sorted(order_depth.buy_orders.keys(), reverse=True):
                        if ask_price <= acceptable_price:
                            break
                        ask_volume = order_depth.buy_orders[ask_price]
                        print("SELL", str(ask_volume) + "x", ask_price)
                        orders.append(Order(product, ask_price, -ask_volume))
                result[product] = orders

            if product == 'BANANAS':
                order_depth: OrderDepth = state.order_depths[product]
                orders: list[Order] = []

                mean_ask_price = get_mean_price(order_depth.sell_orders)
                mean_bid_price = get_mean_price(order_depth.buy_orders)

                #Keep track of product prices
                self.ask_history.append(mean_ask_price)
                self.bid_history.append(mean_bid_price)

                acceptable_price_buy, acceptable_price_sell = self.get_acceptable_price(order_depth, mean_ask_price, mean_bid_price)

                # For stats calculation
                if PRINT_BANANA_ASK_STATS:
                    self.banana_ask_stats.add(order_depth.sell_orders)
                if PRINT_BANANA_BID_STATS:
                    self.banana_bid_stats.add(order_depth.buy_orders)

                if len(order_depth.sell_orders) > 0:
                    for ask_price in sorted(order_depth.sell_orders.keys()):
                        if ask_price >= acceptable_price_buy:
                            break
                        ask_volume = order_depth.sell_orders[ask_price]
                        if len(orders) >= self.max_concurrent_positions:
                            break
                        #if (ask_price - current_price) / current_price < self.stop_loss_percent:
                        #    break
                        #if (ask_price - current_price) / current_price > self.take_profit_percent:
                        #    break
                        print("BUY BANANAS", str(-ask_volume) + "x", ask_price)
                        orders.append(Order(product, ask_price, -ask_volume))

                if len(order_depth.buy_orders) > 0:
                    for bid_price in sorted(order_depth.buy_orders.keys(), reverse=True):
                        if bid_price <= acceptable_price_sell:
                            break
                        bid_volume = order_depth.buy_orders[bid_price]
                        if len(orders) >= self.max_concurrent_positions:
                            break
                        #if (current_price - bid_price) / current_price < self.stop_loss_percent:
                        #    break
                        #if (current_price - bid_price) / current_price > self.take_profit_percent:
                        #    break
                        print("SELL BANANAS", str(bid_volume) + "x", bid_price)
                        orders.append(Order(product, bid_price, bid_volume))

                # Add all the above orders to the result dict
                result[product] = orders


                # Return the dict of orders
                # These possibly contain buy or sell orders for PEARLS
                # Depending on the logic above

        
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

    def print_stats(self):
        flat_list = self.flatten()
        #print(flat_list)
        if len(flat_list) > 10:
            output = "[" + str(self.statistics_type) + ","
            output += "mean:" + str(int(sum(flat_list) / max(1,len(flat_list)))) + ","
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
