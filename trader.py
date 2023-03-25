from typing import Dict, List
import numpy as np
from statistics import mean
from datamodel import OrderDepth, TradingState, Order

COMMODITIES = ["BANANAS", "COCONUTS", "PINA_COLADAS", "DIVING_GEAR", "BERRIES"]
POSITION_LIMITS = {"PEARLS": 20, "BANANAS": 20, "COCONUTS":600, "PINA_COLADAS": 300, "DIVING_GEAR": 50, "BERRIES": 250}
PRINT_PEARL = False
PRINT_PRODUCTS = {"BANANAS": True, "COCONUTS": True, "PINA_COLADAS": True, "BERRIES": True, "DIVING_GEAR": True}
STAT_SLIDING_WINDOW_SIZE = 7

# [CLOSE LONG, OPEN SHORT, CLOSE SHORT, OPEN LONG]
CAN_LONG = {"BANANAS": True, "COCONUTS": True, "PINA_COLADAS": False, "BERRIES": True, "DIVING_GEAR": True}
CAN_SHORT = {"BANANAS": True, "COCONUTS": False, "PINA_COLADAS": True, "BERRIES": True, "DIVING_GEAR": True}

BUY_MARGIN = {"BANANAS": 1, "BERRIES": 1}
SELL_MARGIN = {"BANANAS": 1, "BERRIES": 1}


class Trader:

    def __init__(self):
        self.sliding_window_size = STAT_SLIDING_WINDOW_SIZE
        self.product_stats = {}
        self.sliding_window_means = []
        self.limits = {"PEARLS": 20, "BANANAS": 20, "COCONUTS": 600, "PINA_COLADAS": 300, "DIVING_GEAR": 50,
                           "BERRIES": 250}

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

                if len(order_depth.sell_orders) > 0:
                    # Sort and check whether any orders
                    for ask_price in [sorted(order_depth.sell_orders.keys())[0]]:
                        if ask_price >= acceptable_price + 1:
                            break
                        if ask_price < acceptable_price:
                            ask_volume = order_depth.sell_orders[ask_price]
                            print("BUY PEARLS", str(-ask_volume) + "x", ask_price)
                            orders.append(Order(product, ask_price, -ask_volume))
                        else:
                            ask_volume = POSITION_LIMITS[product] // 4
                            orders.append(Order(product, ask_price, -ask_volume))
                if len(order_depth.buy_orders) != 0:
                    for ask_price in [sorted(order_depth.buy_orders.keys(), reverse=True)[0]]:
                        if ask_price <= acceptable_price - 1:
                            break
                        if ask_price <= acceptable_price:
                            ask_volume = order_depth.buy_orders[ask_price]
                            print("SELL PEARLS", str(ask_volume) + "x", ask_price)
                            orders.append(Order(product, ask_price, -ask_volume))
                        else:
                            ask_volume = POSITION_LIMITS[product] // 4
                            print("SELL PEARLS", str(ask_volume) + "x", ask_price)
                            orders.append(Order(product, ask_price, -ask_volume))
                result[product] = orders
            #elif product == 'PINA_COLADAS' or product == 'COCONUTS':
                # TODO: pair trading
            #    pass
            elif product == 'DIVING_GEAR' or product == 'DOLPHIN_SIGHTINGS':
                # TODO: use dolphin knowledge, DOLPHIN_SIGHTINGS is not a tradable good!
                pass
            else: #! this is now for BANANAS and MAYBERRIES rn
                if product not in self.product_stats.keys():
                    sliding_window_ask = SlidingWindowStatistics(STAT_SLIDING_WINDOW_SIZE, str(product) + "_ASK")
                    sliding_window_bid = SlidingWindowStatistics(STAT_SLIDING_WINDOW_SIZE, str(product) + "_BID")
                    self.product_stats[product] = [sliding_window_ask, sliding_window_bid, {
                        'bid_hist': [],
                        'ask_hist': [],
                        'ask_price': [],
                        'bid_price': []
                    }, [], [], [], []]

                order_depth: OrderDepth = state.order_depths[product]
                orders: list[Order] = []

                sliding_window_ask = self.product_stats[product][0]
                sliding_window_bid = self.product_stats[product][1]
                best_prices = self.product_stats[product][2]
                long_positions = self.product_stats[product][3]
                short_positions = self.product_stats[product][4]
                long_time = self.product_stats[product][5]
                short_time = self.product_stats[product][6]

                if PRINT_PRODUCTS[product]:
                    sliding_window_ask.add(order_depth.sell_orders)
                    sliding_window_bid.add(order_depth.buy_orders)

                if len(order_depth.sell_orders) > 0:
                    ask_price = list(sorted(order_depth.sell_orders.keys()))[0]
                    best_prices['ask_price'].append(ask_price)
                    if len(best_prices['ask_price']) > STAT_SLIDING_WINDOW_SIZE:
                        best_prices['ask_price'].pop(0)

                if len(order_depth.buy_orders) > 0:
                    bid_price = list(sorted(order_depth.buy_orders.keys(), reverse=True))[0]
                    best_prices['bid_price'].append(bid_price)
                    if len(best_prices['bid_price']) > STAT_SLIDING_WINDOW_SIZE:
                        best_prices['bid_price'].pop(0)

                curr_value = 0.5* sum([sum(best_prices[val]) / len(best_prices[val]) for val in ['ask_price', 'bid_price']])

                if ask_price:
                    if ask_price < curr_value:
                        ask_volume = order_depth.sell_orders[ask_price]
                        orders.append(Order(product, ask_price, -ask_volume))
                        short_positions += [ask_price for i in range(abs(ask_volume))]
                    if ask_price - 1 > curr_value:
                        orders.append(Order(product, ask_price - 1, -POSITION_LIMITS[product]//4))
                        short_positions += [ask_price for i in range(abs(POSITION_LIMITS[product]//4))]
                    if ask_price > curr_value:
                        orders.append(Order(product, ask_price, -POSITION_LIMITS[product]//4))
                        short_positions += [ask_price for i in range(abs(POSITION_LIMITS[product]//4))]

                if bid_price:
                    if bid_price > curr_value:
                        bid_volume = order_depth.buy_orders[bid_price]
                        orders.append(Order(product, bid_price, -bid_volume))
                        long_positions += [ask_price for i in range(abs(bid_volume))]
                    if bid_price + 1 < curr_value:
                        orders.append(Order(product, bid_price + 1, POSITION_LIMITS[product] // 4))
                        long_positions += [ask_price for i in range(abs(POSITION_LIMITS[product] // 4))]
                    if bid_price < curr_value:
                        orders.append(Order(product, bid_price, POSITION_LIMITS[product] // 4))
                        long_positions += [ask_price for i in range(abs(POSITION_LIMITS[product] // 4))]

                short_time = list(map(lambda n: n+1, short_time))
                long_time = list(map(lambda n: n+1, long_time))

                self.product_stats[product][0] = sliding_window_ask
                self.product_stats[product][1] = sliding_window_bid
                self.product_stats[product][2] = best_prices
                self.product_stats[product][3] = long_positions
                self.product_stats[product][4] = short_positions
                self.product_stats[product][5] = long_time
                self.product_stats[product][6] = short_time

                # Add all the above orders to the result dict
                result[product] = orders

        for product in state.order_depths.keys():

            if product not in ['PEARLS', 'DIVING_GEAR', 'DOLPHIN_SIGHTINGS']:

                if state.timestamp % (self.sliding_window_size * 2 * 100) == 0:
                    self.sliding_window_means.append(self.product_stats[product][0].get_mean())

                #print(state.position)
                #print(self.product_stats[product][2])
                #print(self.product_stats[product][3])

                # Print stats
                if PRINT_PRODUCTS[product]:
                    self.product_stats[product][0].print_stats()
                    self.product_stats[product][1].print_stats()

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

    def should_act(self, curr_price, buy=True):
        order_depth_dict = self.sliding_window[0]
        if buy:
            min_momentum_price = np.mean(np.array([price for price in order_depth_dict]))
        else:
            min_momentum_price = max([price for price in order_depth_dict])
        momentum = curr_price - min_momentum_price
        if momentum > 0:
            return True
        else:
            return False

    def update_stats(self):
        self.flat_list = self.flatten()
        self.mean = np.mean(np.array(self.flat_list))

    def get_mean(self):
        return self.mean

    def get_min(self):
        if len(self.flat_list) > 0:
            return self.flat_list[0]
        else:
            return 0

    def get_max(self):
        if len(self.flat_list) > 0:
            return self.flat_list[-1:][0]
        else:
            return 0

    def get_percentile(self, perc):
        if len(self.flat_list) > 0:
            return int(np.percentile(np.array(self.flat_list), perc))
        else:
            return 0

    def length(self):
        return len(self.sliding_window)

    def print_stats(self):
        self.update_stats()
        if len(self.flat_list) > 10:
            output = "[" + str(self.statistics_type) + ","
            output += "mean:" + str(self.mean) + ","
            output += "min:" + str(self.get_min()) + ","
            output += "10th:" + str(self.get_percentile(10)) + ","
            output += "25th:" + str(self.get_percentile(25)) + ","
            output += "50th:" + str(self.get_percentile(50)) + ","
            output += "75th:" + str(self.get_percentile(75)) + ","
            output += "90th:" + str(self.get_percentile(90)) + ","
            output += "max:" + str(self.get_max()) + ","
            output += "vol:" + str(len(self.flat_list))
            output += "]"
        else:
            output = "[" + str(self.statistics_type) + ", more data needed]"

        print(output)