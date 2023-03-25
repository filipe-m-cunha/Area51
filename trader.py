from typing import Dict, List
import numpy as np
from statistics import mean
from datamodel import OrderDepth, TradingState, Order

COMMODITIES = ["BANANAS", "COCONUTS", "PINA_COLADAS", "DIVING_GEAR", "MAYBERRIES"]
POSITION_LIMITS = {"PEARLS": 20, "BANANAS": 20, "COCONUTS":600, "PINA_COLADAS": 300, "DIVING_GEAR": 50, "MAYBERRIES": 250}
PRINT_PEARL = False
PRINT_PRODUCTS = {"BANANAS": True, "COCONUTS": True, "PINA_COLADAS": True}
STAT_SLIDING_WINDOW_SIZE = 7

# [CLOSE LONG, OPEN SHORT, CLOSE SHORT, OPEN LONG]
CAN_LONG = {"BANANAS": True, "COCONUTS": True, "PINA_COLADAS": False}
CAN_SHORT = {"BANANAS": True, "COCONUTS": False, "PINA_COLADAS": True}
INITIAL_CONDITIONS = [
    lambda price, slw_bid, slw_ask, positions, volume, time: price > np.mean(np.array(positions[:volume]))\
        or np.mean(np.array(time[:volume])) > 150,
    lambda price, slw_bid, slw_ask, positions, volume, time: price > slw_ask.get_percentile(10)-2 \
        and slw_ask.length() > 2,
    lambda price, slw_bid, slw_ask, positions, volume, time: price < np.mean(np.array(positions[:volume]))\
        or np.mean(np.array(time[:volume])) > 180,
    lambda price, slw_bid, slw_ask, positions, volume, time: price <= slw_bid.get_percentile(90) \
        and slw_bid.length() > 2]

DECISION_CONDITIONS = {"BANANAS": INITIAL_CONDITIONS, "COCONUTS": INITIAL_CONDITIONS, "PINA_COLADAS": [
    lambda price, slw_bid, slw_ask, positions, volume, time: price > np.mean(np.array(positions))\
        or np.mean(np.array(time[:volume])) > 400,
    lambda price, slw_bid, slw_ask, positions, volume, time: price > slw_ask.get_percentile(10)-5 \
        and slw_ask.length() > 2,
    lambda price, slw_bid, slw_ask, positions, volume, time: price < np.mean(np.array(positions[:volume]))\
        or np.mean(np.array(time[:volume])) > 180,
    lambda price, slw_bid, slw_ask, positions, volume, time: price <= slw_bid.get_percentile(90) \
        and slw_bid.length() > 2
]}


class Trader:

    def __init__(self):
        self.sliding_window_size = STAT_SLIDING_WINDOW_SIZE
        self.product_stats = {}
        self.sliding_window_means = []

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
            elif product == 'PINA_COLADAS' or product == 'COCONUTS':
                # TODO: pair trading
                pass
            elif product == 'DIVING_GEAR' or product == 'DOLPHIN_SIGHTINGS':
                # TODO: use dolphin knowledge, DOLPHIN_SIGHTINGS is not a tradable good!
                pass
            else: #! this is now for BANANAS and MAYBERRIES rn
                if product not in self.product_stats.keys():
                    sliding_window_ask = SlidingWindowStatistics(STAT_SLIDING_WINDOW_SIZE, str(product) + "_ASK")
                    sliding_window_bid = SlidingWindowStatistics(STAT_SLIDING_WINDOW_SIZE, str(product) + "_BID")
                    self.product_stats[product] = [sliding_window_ask, sliding_window_bid, [], [], [], []]

                order_depth: OrderDepth = state.order_depths[product]
                orders: list[Order] = []

                sliding_window_ask = self.product_stats[product][0]
                sliding_window_bid = self.product_stats[product][1]
                long_positions = self.product_stats[product][2]
                short_positions = self.product_stats[product][3]
                long_time = self.product_stats[product][4]
                short_time = self.product_stats[product][5]

                if PRINT_PRODUCTS[product]:
                    sliding_window_ask.add(order_depth.sell_orders)
                    sliding_window_bid.add(order_depth.buy_orders)

                if len(order_depth.buy_orders) > 0:
                    num_long_positions = len(long_positions)
                    num_short_positions = len(short_positions)
                    print("bot bid depths: ", str(order_depth.buy_orders))

                    # CLOSE LONG
                    for bid_price in sorted(order_depth.buy_orders.keys(), reverse=True):
                        bid_volume = min(order_depth.buy_orders[bid_price], num_long_positions)
                        # if bid_price > np.mean(np.array(long_positions[:bid_volume])) \
                        #     or np.mean(np.array(long_time[:bid_volume])) > 150 and can_long:
                        if DECISION_CONDITIONS[product][0](bid_price, sliding_window_bid, sliding_window_ask,\
                            long_positions, bid_volume, long_time) and CAN_LONG[product]:
                            #can_short = False
                            print(f"SELL {product} LONG", str(bid_volume) + "x", bid_price)
                            orders.append(Order(product, bid_price, -bid_volume))
                            num_long_positions -= bid_volume
                            long_positions = long_positions[bid_volume:]
                            long_time = long_time[bid_volume:]

                    # OPEN SHORT
                    for bid_price in sorted(order_depth.buy_orders.keys()):
                        bid_volume = min(order_depth.buy_orders[bid_price], POSITION_LIMITS[product] - num_short_positions)
                        # if bid_price > sliding_window_ask.get_percentile(10) - 2 and len(
                        #         sliding_window_ask.sliding_window) > 2 and can_short:
                        if DECISION_CONDITIONS[product][1](bid_price, sliding_window_bid, sliding_window_ask,\
                            short_time, bid_volume, short_time) and CAN_SHORT[product]:
                            print(f"SELL {product} SHORT", str(bid_volume) + "x", bid_price)
                            orders.append(Order(product, bid_price, -bid_volume))
                            num_short_positions += abs(bid_volume)
                            short_positions += [bid_price for x in range(abs(bid_volume))]
                            short_time += [0 for x in range(abs(bid_volume))]

                if len(order_depth.sell_orders) > 0:
                    num_long_positions = len(long_positions)
                    num_short_positions = len(short_positions)

                    # CLOSE SHORT
                    for ask_price in sorted(order_depth.sell_orders.keys(), reverse=True):
                        ask_volume = max(order_depth.sell_orders[ask_price], -(num_short_positions))
                        # bug: should do abs(ask_volume), but nothing has beaten this...
                        # if ask_price < np.mean(np.array(short_positions[:ask_volume])) - 2 \
                        #     or np.mean(np.array(short_time[:ask_volume])) > 180 and can_short:
                        if DECISION_CONDITIONS[product][2](ask_price, sliding_window_bid, sliding_window_ask,\
                            short_positions, ask_volume, short_time) and CAN_SHORT[product]:
                            print(f"BUY {product} SHORT", str(-ask_volume) + "x", ask_price)
                            orders.append(Order(product, ask_price, -ask_volume))
                            num_short_positions -= ask_volume
                            short_positions = short_positions[abs(ask_volume):]
                            short_time = short_time[abs(ask_volume):]

                    # OPEN LONG
                    print("bot ask depths: " + str(order_depth.sell_orders))
                    for ask_price in sorted(order_depth.sell_orders.keys()):
                        ask_volume = max(order_depth.sell_orders[ask_price], -(POSITION_LIMITS[product] - (num_long_positions)))
                        # if ask_price <= sliding_window_bid.get_percentile(90) and len(
                        #     sliding_window_bid.sliding_window) > 2 and can_long:
                        if DECISION_CONDITIONS[product][3](ask_price, sliding_window_bid, sliding_window_ask,\
                            long_positions, ask_volume, long_time) and CAN_LONG[product]:
                            print(f"BUY {product} LONG", str(-ask_volume) + "x", ask_price)
                            orders.append(Order(product, ask_price, -ask_volume))
                            num_long_positions -= ask_volume
                            long_positions += [ask_price for x in range(abs(ask_volume))]
                            long_time += [0 for x in range(abs(ask_volume))]

                short_time = list(map(lambda n: n+1, short_time))
                long_time = list(map(lambda n: n+1, long_time))

                self.product_stats[product][0] = sliding_window_ask
                self.product_stats[product][1] = sliding_window_bid
                self.product_stats[product][2] = long_positions
                self.product_stats[product][3] = short_positions
                self.product_stats[product][4] = long_time
                self.product_stats[product][5] =  short_time

                # Add all the above orders to the result dict
                result[product] = orders

        for product in state.order_depths.keys():

            if product != 'PEARLS':

                if state.timestamp % (self.sliding_window_size * 2 * 100) == 0:
                    self.sliding_window_means.append(self.product_stats[product][0].get_mean())

                print(state.position)
                print(self.product_stats[product][2])
                print(self.product_stats[product][3])

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